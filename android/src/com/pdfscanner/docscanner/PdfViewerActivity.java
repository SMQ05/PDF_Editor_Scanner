package com.pdfscanner.docscanner;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.RectF;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Full-screen PDF viewer activity with annotation tools.
 * 
 * Launch with:
 *   intent.putExtra("pdf_path", "/path/to/file.pdf")
 */
public class PdfViewerActivity extends Activity {
    private static final String TAG = "PdfViewerActivity";
    
    public static final String EXTRA_PDF_PATH = "pdf_path";
    public static final String EXTRA_SAVED_PATH = "saved_path";
    public static final int RESULT_SAVED = 1;
    
    private PdfRenderView pdfRenderView;
    private PdfEditEngine editEngine;
    private String pdfPath;
    private String outputDir;
    
    // UI elements
    private TextView pageIndicator;
    private TextView undoButton, redoButton, saveButton;
    private ProgressBar progressBar;
    
    // State
    private ToolType currentTool = ToolType.NONE;
    private boolean hasUnsavedChanges = false;
    private String pendingSignaturePath;
    private boolean isSaving = false;
    
    private ExecutorService executor = Executors.newSingleThreadExecutor();
    private Handler mainHandler = new Handler(Looper.getMainLooper());
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN);
        
        pdfPath = getIntent().getStringExtra(EXTRA_PDF_PATH);
        if (pdfPath == null || pdfPath.isEmpty()) {
            Toast.makeText(this, "No PDF file specified", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        outputDir = new File(getFilesDir(), "documents").getAbsolutePath();
        
        editEngine = new PdfEditEngine(this);
        
        if (editEngine.isEncrypted(pdfPath)) {
            showEncryptedError();
            return;
        }
        
        // Load document into edit engine
        if (!editEngine.loadDocument(pdfPath)) {
            Toast.makeText(this, "Failed to load PDF", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        buildUI();
        
        if (!pdfRenderView.loadPdf(pdfPath)) {
            Toast.makeText(this, "Failed to render PDF", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        // Initialize undo/redo button state
        updateUndoRedoButtons();
        
        Log.d(TAG, "Opened PDF: " + pdfPath);
    }
    
    private void buildUI() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.DKGRAY);
        
        // PDF render view
        pdfRenderView = new PdfRenderView(this);
        pdfRenderView.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(pdfRenderView);
        
        // Listeners
        pdfRenderView.setOnPageChangeListener((pageIndex, pageCount) -> {
            updatePageIndicator(pageIndex, pageCount);
        });
        
        pdfRenderView.setOnAnnotationListener(() -> {
            hasUnsavedChanges = true;
            updateUndoRedoButtons();
        });
        
        pdfRenderView.setOnTextRectListener(this::showTextInputDialog);
        pdfRenderView.setOnSignatureRectListener(this::placeSignatureAtRect);
        
        // Top toolbar
        LinearLayout toolbar = createToolbar();
        FrameLayout.LayoutParams toolbarParams = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, dpToPx(56));
        root.addView(toolbar, toolbarParams);
        
        // Bottom tool palette
        LinearLayout toolPalette = createToolPalette();
        FrameLayout.LayoutParams paletteParams = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, dpToPx(60));
        paletteParams.gravity = Gravity.BOTTOM;
        root.addView(toolPalette, paletteParams);
        
        // Progress bar
        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setIndeterminate(true);
        progressBar.setVisibility(View.GONE);
        FrameLayout.LayoutParams progressParams = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, dpToPx(4));
        progressParams.gravity = Gravity.TOP;
        progressParams.topMargin = dpToPx(56);
        root.addView(progressBar, progressParams);
        
        setContentView(root);
    }
    
    private LinearLayout createToolbar() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setBackgroundColor(Color.argb(220, 30, 30, 30));
        bar.setPadding(dpToPx(8), dpToPx(8), dpToPx(8), dpToPx(8));
        bar.setGravity(Gravity.CENTER_VERTICAL);
        
        bar.addView(createToolButton("←", v -> confirmExit()));
        
        // Page navigation buttons
        bar.addView(createToolButton("◄", v -> pdfRenderView.previousPage()));
        
        pageIndicator = new TextView(this);
        pageIndicator.setTextColor(Color.WHITE);
        pageIndicator.setTextSize(14);
        pageIndicator.setPadding(dpToPx(8), 0, dpToPx(8), 0);
        pageIndicator.setText("Page 1/1");
        pageIndicator.setClickable(true);
        pageIndicator.setOnClickListener(v -> showPageJumpDialog());
        bar.addView(pageIndicator);
        
        bar.addView(createToolButton("►", v -> pdfRenderView.nextPage()));
        
        // Spacer
        View spacer = new View(this);
        bar.addView(spacer, new LinearLayout.LayoutParams(0, 1, 1f));
        
        undoButton = createToolButton("↩", v -> {
            if (pdfRenderView.undo()) {
                hasUnsavedChanges = true;
                updateUndoRedoButtons();
            }
        });
        bar.addView(undoButton);
        
        redoButton = createToolButton("↪", v -> {
            if (pdfRenderView.redo()) {
                hasUnsavedChanges = true;
                updateUndoRedoButtons();
            }
        });
        bar.addView(redoButton);
        
        saveButton = createToolButton("💾", v -> {
            if (!isSaving) {
                showSaveDialog();
            }
        });
        bar.addView(saveButton);
        
        bar.addView(createToolButton("📤", v -> shareCurrentPdf()));
        
        return bar;
    }
    
    private LinearLayout createToolPalette() {
        LinearLayout palette = new LinearLayout(this);
        palette.setOrientation(LinearLayout.HORIZONTAL);
        palette.setBackgroundColor(Color.argb(220, 30, 30, 30));
        palette.setPadding(dpToPx(4), dpToPx(8), dpToPx(4), dpToPx(8));
        palette.setGravity(Gravity.CENTER);
        
        palette.addView(createToolButton("✋", v -> selectTool(ToolType.NONE)));
        
        palette.addView(createToolButton("🖍", v -> {
            pdfRenderView.setToolColor(Color.YELLOW);
            selectTool(ToolType.HIGHLIGHT);
        }));
        
        palette.addView(createToolButton("U̲", v -> {
            pdfRenderView.setToolColor(Color.BLUE);
            selectTool(ToolType.UNDERLINE);
        }));
        
        palette.addView(createToolButton("S̶", v -> {
            pdfRenderView.setToolColor(Color.RED);
            selectTool(ToolType.STRIKEOUT);
        }));
        
        palette.addView(createToolButton("✏", v -> {
            pdfRenderView.setToolColor(Color.BLACK);
            selectTool(ToolType.PEN);
        }));
        
        palette.addView(createToolButton("█", v -> selectTool(ToolType.REDACT_BLACK)));
        palette.addView(createToolButton("▢", v -> selectTool(ToolType.REDACT_WHITE)));
        
        palette.addView(createToolButton("T", v -> {
            pdfRenderView.setToolColor(Color.BLACK);
            selectTool(ToolType.TEXT);
            Toast.makeText(this, "Draw rectangle for text", Toast.LENGTH_SHORT).show();
        }));
        
        palette.addView(createToolButton("✍", v -> showSignatureDialog()));
        
        return palette;
    }
    
    /**
     * Creates a clickable tool button (TextView styled as button).
     */
    private TextView createToolButton(String emoji, View.OnClickListener listener) {
        TextView tv = new TextView(this);
        tv.setText(emoji);
        tv.setTextSize(20);
        tv.setTextColor(Color.WHITE);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(dpToPx(12), dpToPx(8), dpToPx(12), dpToPx(8));
        tv.setClickable(true);
        tv.setFocusable(true);
        tv.setOnClickListener(listener);
        
        // Add ripple effect background
        tv.setBackgroundResource(android.R.drawable.list_selector_background);
        
        return tv;
    }
    
    private void selectTool(ToolType tool) {
        currentTool = tool;
        pdfRenderView.setCurrentTool(tool);
        
        String toolName = tool == ToolType.NONE ? "Pan/Zoom" : tool.name();
        Toast.makeText(this, toolName, Toast.LENGTH_SHORT).show();
    }
    
    private void updatePageIndicator(int pageIndex, int pageCount) {
        pageIndicator.setText(String.format(Locale.US, "Page %d/%d", pageIndex + 1, pageCount));
    }
    
    private void updateUndoRedoButtons() {
        if (undoButton != null) {
            undoButton.setAlpha(pdfRenderView.canUndo() ? 1.0f : 0.3f);
            undoButton.setEnabled(pdfRenderView.canUndo());
        }
        if (redoButton != null) {
            redoButton.setAlpha(pdfRenderView.canRedo() ? 1.0f : 0.3f);
            redoButton.setEnabled(pdfRenderView.canRedo());
        }
    }
    
    private void showPageJumpDialog() {
        int totalPages = pdfRenderView.getPageCount();
        if (totalPages <= 1) return;
        
        EditText input = new EditText(this);
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        input.setHint("Page (1-" + totalPages + ")");
        
        new AlertDialog.Builder(this)
            .setTitle("Jump to Page")
            .setView(input)
            .setPositiveButton("Go", (d, w) -> {
                try {
                    int page = Integer.parseInt(input.getText().toString().trim());
                    if (page >= 1 && page <= totalPages) {
                        pdfRenderView.goToPage(page - 1);  // 0-indexed
                    } else {
                        Toast.makeText(this, "Invalid page number", Toast.LENGTH_SHORT).show();
                    }
                } catch (NumberFormatException e) {
                    Toast.makeText(this, "Invalid input", Toast.LENGTH_SHORT).show();
                }
            })
            .setNegativeButton("Cancel", null)
            .show();
    }
    
    private void showEncryptedError() {
        new AlertDialog.Builder(this)
            .setTitle("Cannot Open PDF")
            .setMessage("Password-protected PDFs are not supported.")
            .setPositiveButton("OK", (d, w) -> finish())
            .setCancelable(false)
            .show();
    }
    
    // ========== Text Input Dialog ==========
    
    private void showTextInputDialog(RectF rect) {
        EditText input = new EditText(this);
        input.setHint("Enter text");
        input.setSingleLine(false);
        input.setMinLines(2);
        
        new AlertDialog.Builder(this)
            .setTitle("Add Text")
            .setView(input)
            .setPositiveButton("Add", (d, w) -> {
                String text = input.getText().toString().trim();
                if (!text.isEmpty()) {
                    pdfRenderView.addTextAnnotation(rect, text, 14f);
                    hasUnsavedChanges = true;
                    updateUndoRedoButtons();
                }
                selectTool(ToolType.NONE);
            })
            .setNegativeButton("Cancel", (d, w) -> {
                pdfRenderView.clearPendingRects();
                selectTool(ToolType.NONE);
            })
            .setOnCancelListener(d -> {
                pdfRenderView.clearPendingRects();
                selectTool(ToolType.NONE);
            })
            .show();
    }
    
    // ========== Signature ==========
    
    private void showSignatureDialog() {
        FrameLayout container = new FrameLayout(this);
        container.setPadding(dpToPx(16), dpToPx(16), dpToPx(16), dpToPx(16));
        
        SignaturePadView signaturePad = new SignaturePadView(this);
        signaturePad.setBackgroundColor(Color.WHITE);
        FrameLayout.LayoutParams padParams = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, dpToPx(200));
        container.addView(signaturePad, padParams);
        
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("Draw Signature")
            .setView(container)
            .setPositiveButton("Place", null)  // Override below
            .setNeutralButton("Clear", null)
            .setNegativeButton("Cancel", null)
            .create();
        
        dialog.show();
        
        // Override positive button to not dismiss if no signature
        dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            if (signaturePad.hasSignature()) {
                exportAndPlaceSignature(signaturePad);
                dialog.dismiss();
            } else {
                Toast.makeText(this, "Draw a signature first", Toast.LENGTH_SHORT).show();
            }
        });
        
        dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v -> {
            signaturePad.clear();
        });
    }
    
    private void exportAndPlaceSignature(SignaturePadView signaturePad) {
        File cacheDir = getCacheDir();
        String sigPath = new File(cacheDir, "signature_" + System.currentTimeMillis() + ".png")
            .getAbsolutePath();
        
        if (signaturePad.exportToPng(sigPath)) {
            pendingSignaturePath = sigPath;
            selectTool(ToolType.SIGNATURE);
            Toast.makeText(this, "Draw rectangle to place signature", Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "Failed to export signature", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void placeSignatureAtRect(RectF rect) {
        if (pendingSignaturePath != null && rect != null) {
            pdfRenderView.addSignatureAnnotation(pendingSignaturePath, rect);
            hasUnsavedChanges = true;
            updateUndoRedoButtons();
            pendingSignaturePath = null;
        }
        selectTool(ToolType.NONE);
    }
    
    // ========== Save / Share ==========
    
    private void showSaveDialog() {
        String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
        String defaultName = "Edited_" + timestamp;
        
        EditText input = new EditText(this);
        input.setText(defaultName);
        input.setSelectAllOnFocus(true);
        
        new AlertDialog.Builder(this)
            .setTitle("Save As")
            .setView(input)
            .setPositiveButton("Save", (d, w) -> {
                String filename = input.getText().toString().trim();
                if (filename.isEmpty()) filename = defaultName;
                if (!filename.toLowerCase().endsWith(".pdf")) filename += ".pdf";
                saveDocument(filename);
            })
            .setNegativeButton("Cancel", null)
            .show();
    }
    
    private void saveDocument(String filename) {
        if (isSaving) return;  // Prevent double-saves
        
        isSaving = true;
        progressBar.setVisibility(View.VISIBLE);
        if (saveButton != null) {
            saveButton.setEnabled(false);
            saveButton.setAlpha(0.5f);
        }
        
        executor.execute(() -> {
            try {
                File outDir = new File(outputDir);
                if (!outDir.exists()) outDir.mkdirs();
                
                String outputPath = new File(outDir, filename).getAbsolutePath();
                
                // Use stateless save with annotations
                boolean success = editEngine.saveWithAnnotations(
                    pdfRenderView.getAnnotations(), outputPath);
                
                mainHandler.post(() -> {
                    progressBar.setVisibility(View.GONE);
                    isSaving = false;
                    if (saveButton != null) {
                        saveButton.setEnabled(true);
                        saveButton.setAlpha(1.0f);
                    }
                    
                    if (success) {
                        hasUnsavedChanges = false;
                        Toast.makeText(this, "✓ Saved: " + filename, Toast.LENGTH_SHORT).show();
                        
                        android.content.Intent result = new android.content.Intent();
                        result.putExtra(EXTRA_SAVED_PATH, outputPath);
                        setResult(RESULT_SAVED, result);
                    } else {
                        Toast.makeText(this, "✗ Save failed", Toast.LENGTH_SHORT).show();
                    }
                });
                
            } catch (Exception e) {
                Log.e(TAG, "Save error: " + e.getMessage());
                mainHandler.post(() -> {
                    progressBar.setVisibility(View.GONE);
                    isSaving = false;
                    if (saveButton != null) {
                        saveButton.setEnabled(true);
                        saveButton.setAlpha(1.0f);
                    }
                    Toast.makeText(this, "✗ Save error", Toast.LENGTH_SHORT).show();
                });
            }
        });
    }
    
    private void shareCurrentPdf() {
        if (hasUnsavedChanges) {
            new AlertDialog.Builder(this)
                .setTitle("Save Changes?")
                .setMessage("Save before sharing?")
                .setPositiveButton("Save & Share", (d, w) -> {
                    String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
                    saveAndShare("Edited_" + timestamp + ".pdf");
                })
                .setNegativeButton("Share Original", (d, w) -> doShare(pdfPath))
                .setNeutralButton("Cancel", null)
                .show();
        } else {
            doShare(pdfPath);
        }
    }
    
    private void saveAndShare(String filename) {
        if (isSaving) return;
        
        isSaving = true;
        progressBar.setVisibility(View.VISIBLE);
        
        executor.execute(() -> {
            try {
                File outDir = new File(outputDir);
                if (!outDir.exists()) outDir.mkdirs();
                
                String outputPath = new File(outDir, filename).getAbsolutePath();
                boolean success = editEngine.saveWithAnnotations(
                    pdfRenderView.getAnnotations(), outputPath);
                
                mainHandler.post(() -> {
                    progressBar.setVisibility(View.GONE);
                    isSaving = false;
                    
                    if (success) {
                        hasUnsavedChanges = false;
                        doShare(outputPath);
                    } else {
                        Toast.makeText(this, "Save failed", Toast.LENGTH_SHORT).show();
                    }
                });
                
            } catch (Exception e) {
                mainHandler.post(() -> {
                    progressBar.setVisibility(View.GONE);
                    isSaving = false;
                    Toast.makeText(this, "Error", Toast.LENGTH_SHORT).show();
                });
            }
        });
    }
    
    private void doShare(String filePath) {
        IntentUtils.shareFile(this, filePath, "application/pdf", "Share PDF");
    }
    
    // ========== Lifecycle ==========
    
    private void confirmExit() {
        if (hasUnsavedChanges) {
            new AlertDialog.Builder(this)
                .setTitle("Unsaved Changes")
                .setMessage("Discard changes?")
                .setPositiveButton("Discard", (d, w) -> finish())
                .setNegativeButton("Cancel", null)
                .show();
        } else {
            finish();
        }
    }
    
    @Override
    public void onBackPressed() {
        confirmExit();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        
        if (pdfRenderView != null) {
            pdfRenderView.closePdf();
        }
        if (editEngine != null) {
            editEngine.closeDocument();
        }
        if (executor != null && !executor.isShutdown()) {
            executor.shutdown();
        }
    }
    
    private int dpToPx(int dp) {
        return (int) (dp * getResources().getDisplayMetrics().density);
    }
}
