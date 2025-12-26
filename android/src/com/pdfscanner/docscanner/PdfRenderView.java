package com.pdfscanner.docscanner;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PointF;
import android.graphics.RectF;
import android.graphics.pdf.PdfRenderer;
import android.os.ParcelFileDescriptor;
import android.util.AttributeSet;
import android.util.Log;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.View;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Custom view for rendering and interacting with PDF pages.
 * 
 * COORDINATE SYSTEM:
 * - VIEW space: Screen pixels (touch events)
 * - BITMAP space: Rendered bitmap pixels (150 DPI)
 * - PDF space: PDF page points (72 DPI) - THIS IS WHERE ANNOTATIONS ARE STORED
 * 
 * All annotations are stored in PDF point coordinates for accurate placement
 * when saved to output PDF.
 */
public class PdfRenderView extends View {
    private static final String TAG = "PdfRenderView";
    private static final int RENDER_DPI = 150;
    
    // Rendering
    private PdfRenderer pdfRenderer;
    private ParcelFileDescriptor fileDescriptor;
    private PdfRenderer.Page currentPage;
    private Bitmap pageBitmap;
    private int currentPageIndex = 0;
    private int pageCount = 0;
    
    // Page dimensions in PDF points (72 DPI)
    private int pageWidthPoints = 0;
    private int pageHeightPoints = 0;
    
    // Coordinate conversion: bitmap pixels <-> PDF points
    private float bitmapToPdfScale = 72f / RENDER_DPI;  // 0.48 for 150 DPI
    
    // Transforms for view
    private Matrix displayMatrix = new Matrix();
    private Matrix inverseMatrix = new Matrix();
    private float scale = 1.0f;
    private float minScale = 0.5f;
    private float maxScale = 5.0f;
    private float panX = 0, panY = 0;
    
    // Paint
    private Paint bitmapPaint;
    private Paint annotationPaint;
    
    // Gestures
    private ScaleGestureDetector scaleDetector;
    private GestureDetector gestureDetector;
    private boolean isScaling = false;
    
    // Tool state
    private ToolType currentTool = ToolType.NONE;
    private int toolColor = Color.YELLOW;
    private float toolStrokeWidth = 4f;
    
    // Current drawing (in BITMAP coordinates during touch, converted to PDF on finalize)
    private RectF currentRectBitmap;
    private List<PointF> currentStrokeBitmap;
    private PointF startPointBitmap;
    
    // Annotations storage (in PDF point coordinates)
    private AnnotationData.DocumentAnnotations annotations;
    
    // Listeners
    public interface OnPageChangeListener {
        void onPageChanged(int pageIndex, int pageCount);
    }
    public interface OnAnnotationListener {
        void onAnnotationAdded();
    }
    public interface OnTextRectListener {
        void onTextRectSelected(RectF rectInPdfPoints);
    }
    public interface OnSignatureRectListener {
        void onSignatureRectSelected(RectF rectInPdfPoints);
    }
    
    private OnPageChangeListener pageChangeListener;
    private OnAnnotationListener annotationListener;
    private OnTextRectListener textRectListener;
    private OnSignatureRectListener signatureRectListener;
    
    public PdfRenderView(Context context) {
        super(context);
        init(context);
    }
    
    public PdfRenderView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init(context);
    }
    
    public PdfRenderView(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
        init(context);
    }
    
    private void init(Context context) {
        bitmapPaint = new Paint();
        bitmapPaint.setAntiAlias(true);
        bitmapPaint.setFilterBitmap(true);
        
        annotationPaint = new Paint();
        annotationPaint.setAntiAlias(true);
        annotationPaint.setStyle(Paint.Style.STROKE);
        annotationPaint.setStrokeWidth(4f);
        annotationPaint.setStrokeCap(Paint.Cap.ROUND);
        
        annotations = new AnnotationData.DocumentAnnotations();
        currentStrokeBitmap = new ArrayList<>();
        
        scaleDetector = new ScaleGestureDetector(context, new ScaleListener());
        gestureDetector = new GestureDetector(context, new GestureListener());
    }
    
    // ========== Coordinate Conversion ==========
    
    /**
     * Convert bitmap pixel rectangle to PDF point rectangle.
     */
    private RectF bitmapToPdfRect(RectF bitmapRect) {
        if (bitmapRect == null) return null;
        return new RectF(
            bitmapRect.left * bitmapToPdfScale,
            bitmapRect.top * bitmapToPdfScale,
            bitmapRect.right * bitmapToPdfScale,
            bitmapRect.bottom * bitmapToPdfScale
        );
    }
    
    /**
     * Convert bitmap pixel point to PDF point.
     */
    private PointF bitmapToPdfPoint(PointF bitmapPoint) {
        if (bitmapPoint == null) return null;
        return new PointF(
            bitmapPoint.x * bitmapToPdfScale,
            bitmapPoint.y * bitmapToPdfScale
        );
    }
    
    /**
     * Convert PDF point rectangle to bitmap pixel rectangle for drawing.
     */
    private RectF pdfToBitmapRect(RectF pdfRect) {
        if (pdfRect == null) return null;
        float pdfToBitmapScale = 1.0f / bitmapToPdfScale;
        return new RectF(
            pdfRect.left * pdfToBitmapScale,
            pdfRect.top * pdfToBitmapScale,
            pdfRect.right * pdfToBitmapScale,
            pdfRect.bottom * pdfToBitmapScale
        );
    }
    
    /**
     * Convert list of bitmap points to PDF points.
     */
    private List<PointF> bitmapToPdfPoints(List<PointF> bitmapPoints) {
        List<PointF> pdfPoints = new ArrayList<>();
        for (PointF bp : bitmapPoints) {
            pdfPoints.add(bitmapToPdfPoint(bp));
        }
        return pdfPoints;
    }
    
    // ========== PDF Loading ==========
    
    public boolean loadPdf(String filePath) {
        try {
            closePdf();
            
            File file = new File(filePath);
            if (!file.exists()) {
                Log.e(TAG, "File not found: " + filePath);
                return false;
            }
            
            fileDescriptor = ParcelFileDescriptor.open(file,
                ParcelFileDescriptor.MODE_READ_ONLY);
            
            pdfRenderer = new PdfRenderer(fileDescriptor);
            pageCount = pdfRenderer.getPageCount();
            currentPageIndex = 0;
            
            Log.d(TAG, "Loaded PDF with " + pageCount + " pages");
            
            renderCurrentPage();
            return true;
            
        } catch (Exception e) {
            Log.e(TAG, "Failed to load PDF: " + e.getMessage());
            return false;
        }
    }
    
    private void renderCurrentPage() {
        if (pdfRenderer == null || pageCount == 0) return;
        
        try {
            if (currentPage != null) {
                currentPage.close();
            }
            
            currentPage = pdfRenderer.openPage(currentPageIndex);
            
            // Store page dimensions in PDF points
            pageWidthPoints = currentPage.getWidth();
            pageHeightPoints = currentPage.getHeight();
            
            // Calculate bitmap size
            int bitmapWidth = (int) (pageWidthPoints * RENDER_DPI / 72f);
            int bitmapHeight = (int) (pageHeightPoints * RENDER_DPI / 72f);
            
            // Update scale factor
            bitmapToPdfScale = 72f / RENDER_DPI;
            
            Log.d(TAG, String.format("Page %d: %dx%d points, bitmap %dx%d px, scale=%.3f",
                currentPageIndex, pageWidthPoints, pageHeightPoints,
                bitmapWidth, bitmapHeight, bitmapToPdfScale));
            
            // Recycle old bitmap
            if (pageBitmap != null) {
                pageBitmap.recycle();
            }
            
            pageBitmap = Bitmap.createBitmap(bitmapWidth, bitmapHeight, Bitmap.Config.ARGB_8888);
            pageBitmap.eraseColor(Color.WHITE);
            
            currentPage.render(pageBitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
            
            fitToScreen();
            
            if (pageChangeListener != null) {
                pageChangeListener.onPageChanged(currentPageIndex, pageCount);
            }
            
            invalidate();
            
        } catch (Exception e) {
            Log.e(TAG, "Failed to render page: " + e.getMessage());
        }
    }
    
    private void fitToScreen() {
        if (pageBitmap == null || getWidth() == 0 || getHeight() == 0) return;
        
        float scaleX = (float) getWidth() / pageBitmap.getWidth();
        float scaleY = (float) getHeight() / pageBitmap.getHeight();
        scale = Math.min(scaleX, scaleY);
        
        panX = (getWidth() - pageBitmap.getWidth() * scale) / 2;
        panY = (getHeight() - pageBitmap.getHeight() * scale) / 2;
        
        updateMatrix();
    }
    
    private void updateMatrix() {
        displayMatrix.reset();
        displayMatrix.postScale(scale, scale);
        displayMatrix.postTranslate(panX, panY);
        displayMatrix.invert(inverseMatrix);
    }
    
    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        if (pageBitmap != null) {
            fitToScreen();
        }
    }
    
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        
        canvas.drawColor(Color.DKGRAY);
        
        if (pageBitmap != null) {
            canvas.save();
            canvas.concat(displayMatrix);
            canvas.drawBitmap(pageBitmap, 0, 0, bitmapPaint);
            
            // Draw existing annotations (convert from PDF to bitmap for display)
            drawAnnotations(canvas);
            
            // Draw current drawing (already in bitmap coords)
            drawCurrentDrawing(canvas);
            
            canvas.restore();
        }
    }
    
    private void drawAnnotations(Canvas canvas) {
        List<AnnotationData.Annotation> pageAnnotations = 
            annotations.getAnnotationsForPage(currentPageIndex);
        
        for (AnnotationData.Annotation ann : pageAnnotations) {
            if (ann instanceof AnnotationData.MarkupAnnotation) {
                drawMarkupAnnotation(canvas, (AnnotationData.MarkupAnnotation) ann);
            } else if (ann instanceof AnnotationData.InkAnnotation) {
                drawInkAnnotation(canvas, (AnnotationData.InkAnnotation) ann);
            } else if (ann instanceof AnnotationData.RedactionAnnotation) {
                drawRedactionAnnotation(canvas, (AnnotationData.RedactionAnnotation) ann);
            } else if (ann instanceof AnnotationData.TextAnnotation) {
                drawTextAnnotation(canvas, (AnnotationData.TextAnnotation) ann);
            }
        }
    }
    
    private void drawMarkupAnnotation(Canvas canvas, AnnotationData.MarkupAnnotation markup) {
        // Convert PDF coords to bitmap coords for drawing
        RectF bitmapRect = pdfToBitmapRect(markup.rect);
        if (bitmapRect == null) return;
        
        Paint paint = new Paint();
        paint.setAntiAlias(true);
        
        switch (markup.type) {
            case HIGHLIGHT:
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(Color.argb(80, Color.red(markup.color), 
                    Color.green(markup.color), Color.blue(markup.color)));
                canvas.drawRect(bitmapRect, paint);
                break;
                
            case UNDERLINE:
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(markup.color);
                paint.setStrokeWidth(2);
                canvas.drawLine(bitmapRect.left, bitmapRect.bottom, 
                    bitmapRect.right, bitmapRect.bottom, paint);
                break;
                
            case STRIKEOUT:
                paint.setStyle(Paint.Style.STROKE);
                paint.setColor(markup.color);
                paint.setStrokeWidth(2);
                float y = bitmapRect.centerY();
                canvas.drawLine(bitmapRect.left, y, bitmapRect.right, y, paint);
                break;
        }
    }
    
    private void drawInkAnnotation(Canvas canvas, AnnotationData.InkAnnotation ink) {
        Paint paint = new Paint();
        paint.setAntiAlias(true);
        paint.setStyle(Paint.Style.STROKE);
        paint.setColor(ink.color);
        paint.setStrokeWidth(ink.strokeWidth / bitmapToPdfScale);  // Adjust width for display
        paint.setStrokeCap(Paint.Cap.ROUND);
        
        for (List<PointF> pdfStroke : ink.strokes) {
            if (pdfStroke.size() < 2) continue;
            
            Path path = new Path();
            
            // Convert PDF points to bitmap for drawing
            PointF firstPdf = pdfStroke.get(0);
            float pdfToBitmap = 1.0f / bitmapToPdfScale;
            float firstX = firstPdf.x * pdfToBitmap;
            float firstY = firstPdf.y * pdfToBitmap;
            path.moveTo(firstX, firstY);
            
            for (int i = 1; i < pdfStroke.size(); i++) {
                PointF pdfPt = pdfStroke.get(i);
                float bitmapX = pdfPt.x * pdfToBitmap;
                float bitmapY = pdfPt.y * pdfToBitmap;
                path.lineTo(bitmapX, bitmapY);
            }
            
            canvas.drawPath(path, paint);
        }
    }
    
    private void drawRedactionAnnotation(Canvas canvas, AnnotationData.RedactionAnnotation redact) {
        RectF bitmapRect = pdfToBitmapRect(redact.rect);
        if (bitmapRect == null) return;
        
        Paint paint = new Paint();
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(redact.isBlack ? Color.BLACK : Color.WHITE);
        canvas.drawRect(bitmapRect, paint);
    }
    
    private void drawTextAnnotation(Canvas canvas, AnnotationData.TextAnnotation text) {
        RectF bitmapRect = pdfToBitmapRect(text.rect);
        if (bitmapRect == null) return;
        
        Paint paint = new Paint();
        paint.setAntiAlias(true);
        paint.setColor(text.color);
        float bitmapFontSize = text.fontSize / bitmapToPdfScale;
        paint.setTextSize(bitmapFontSize);
        canvas.drawText(text.text, bitmapRect.left, bitmapRect.top + bitmapFontSize, paint);
    }
    
    private void drawCurrentDrawing(Canvas canvas) {
        if (currentTool == ToolType.NONE) return;
        
        switch (currentTool) {
            case HIGHLIGHT:
            case UNDERLINE:
            case STRIKEOUT:
            case REDACT_BLACK:
            case REDACT_WHITE:
            case TEXT:
            case SIGNATURE:
                if (currentRectBitmap != null) {
                    Paint paint = new Paint();
                    paint.setStyle(Paint.Style.STROKE);
                    paint.setColor(toolColor);
                    paint.setStrokeWidth(2);
                    paint.setPathEffect(new android.graphics.DashPathEffect(
                        new float[]{10, 10}, 0));
                    canvas.drawRect(currentRectBitmap, paint);
                }
                break;
                
            case PEN:
                if (!currentStrokeBitmap.isEmpty()) {
                    Path path = new Path();
                    PointF first = currentStrokeBitmap.get(0);
                    path.moveTo(first.x, first.y);
                    
                    for (int i = 1; i < currentStrokeBitmap.size(); i++) {
                        path.lineTo(currentStrokeBitmap.get(i).x, currentStrokeBitmap.get(i).y);
                    }
                    
                    annotationPaint.setColor(toolColor);
                    annotationPaint.setStrokeWidth(toolStrokeWidth);
                    canvas.drawPath(path, annotationPaint);
                }
                break;
        }
    }
    
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (currentTool == ToolType.NONE) {
            scaleDetector.onTouchEvent(event);
            gestureDetector.onTouchEvent(event);
            return true;
        }
        
        return handleAnnotationTouch(event);
    }
    
    private boolean handleAnnotationTouch(MotionEvent event) {
        float x = event.getX();
        float y = event.getY();
        
        // Convert screen to bitmap coordinates
        float[] pts = new float[]{x, y};
        inverseMatrix.mapPoints(pts);
        float bitmapX = pts[0];
        float bitmapY = pts[1];
        
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                startPointBitmap = new PointF(bitmapX, bitmapY);
                
                if (currentTool == ToolType.PEN) {
                    currentStrokeBitmap.clear();
                    currentStrokeBitmap.add(new PointF(bitmapX, bitmapY));
                } else {
                    currentRectBitmap = new RectF(bitmapX, bitmapY, bitmapX, bitmapY);
                }
                invalidate();
                return true;
                
            case MotionEvent.ACTION_MOVE:
                if (currentTool == ToolType.PEN) {
                    currentStrokeBitmap.add(new PointF(bitmapX, bitmapY));
                } else if (currentRectBitmap != null && startPointBitmap != null) {
                    currentRectBitmap.left = Math.min(startPointBitmap.x, bitmapX);
                    currentRectBitmap.top = Math.min(startPointBitmap.y, bitmapY);
                    currentRectBitmap.right = Math.max(startPointBitmap.x, bitmapX);
                    currentRectBitmap.bottom = Math.max(startPointBitmap.y, bitmapY);
                }
                invalidate();
                return true;
                
            case MotionEvent.ACTION_UP:
                finalizeAnnotation();
                invalidate();
                return true;
        }
        
        return false;
    }
    
    private void finalizeAnnotation() {
        AnnotationData.Annotation annotation = null;
        
        // Convert bitmap coordinates to PDF coordinates before storing
        RectF pdfRect = bitmapToPdfRect(currentRectBitmap);
        
        switch (currentTool) {
            case HIGHLIGHT:
                if (pdfRect != null && pdfRect.width() > 2) {
                    annotation = new AnnotationData.MarkupAnnotation(
                        currentPageIndex, pdfRect, 
                        ToolType.HIGHLIGHT, toolColor);
                }
                break;
                
            case UNDERLINE:
                if (pdfRect != null && pdfRect.width() > 2) {
                    annotation = new AnnotationData.MarkupAnnotation(
                        currentPageIndex, pdfRect,
                        ToolType.UNDERLINE, toolColor);
                }
                break;
                
            case STRIKEOUT:
                if (pdfRect != null && pdfRect.width() > 2) {
                    annotation = new AnnotationData.MarkupAnnotation(
                        currentPageIndex, pdfRect,
                        ToolType.STRIKEOUT, Color.RED);
                }
                break;
                
            case PEN:
                if (currentStrokeBitmap.size() > 2) {
                    // Convert bitmap stroke to PDF points
                    List<PointF> pdfStroke = bitmapToPdfPoints(currentStrokeBitmap);
                    AnnotationData.InkAnnotation ink = new AnnotationData.InkAnnotation(
                        currentPageIndex, toolColor, toolStrokeWidth * bitmapToPdfScale);
                    ink.addStroke(pdfStroke);
                    annotation = ink;
                }
                currentStrokeBitmap.clear();
                break;
                
            case REDACT_BLACK:
                if (pdfRect != null && pdfRect.width() > 2) {
                    annotation = new AnnotationData.RedactionAnnotation(
                        currentPageIndex, pdfRect, true);
                }
                break;
                
            case REDACT_WHITE:
                if (pdfRect != null && pdfRect.width() > 2) {
                    annotation = new AnnotationData.RedactionAnnotation(
                        currentPageIndex, pdfRect, false);
                }
                break;
                
            case TEXT:
                if (pdfRect != null && pdfRect.width() > 2 && pdfRect.height() > 2) {
                    if (textRectListener != null) {
                        textRectListener.onTextRectSelected(pdfRect);
                    }
                }
                currentRectBitmap = null;
                startPointBitmap = null;
                return;  // Don't add annotation yet
                
            case SIGNATURE:
                if (pdfRect != null && pdfRect.width() > 10 && pdfRect.height() > 5) {
                    if (signatureRectListener != null) {
                        signatureRectListener.onSignatureRectSelected(pdfRect);
                    }
                }
                currentRectBitmap = null;
                startPointBitmap = null;
                return;
        }
        
        if (annotation != null) {
            annotations.add(annotation);
            if (annotationListener != null) {
                annotationListener.onAnnotationAdded();
            }
        }
        
        currentRectBitmap = null;
        startPointBitmap = null;
    }
    
    // ========== Public API ==========
    
    public void setCurrentTool(ToolType tool) {
        this.currentTool = tool;
    }
    
    public ToolType getCurrentTool() {
        return currentTool;
    }
    
    public void setToolColor(int color) {
        this.toolColor = color;
    }
    
    public void setToolStrokeWidth(float width) {
        this.toolStrokeWidth = width;
    }
    
    public void nextPage() {
        if (currentPageIndex < pageCount - 1) {
            currentPageIndex++;
            renderCurrentPage();
        }
    }
    
    public void previousPage() {
        if (currentPageIndex > 0) {
            currentPageIndex--;
            renderCurrentPage();
        }
    }
    
    public void goToPage(int pageIndex) {
        if (pageIndex >= 0 && pageIndex < pageCount) {
            currentPageIndex = pageIndex;
            renderCurrentPage();
        }
    }
    
    public int getCurrentPageIndex() {
        return currentPageIndex;
    }
    
    public int getPageCount() {
        return pageCount;
    }
    
    public AnnotationData.DocumentAnnotations getAnnotations() {
        return annotations;
    }
    
    public boolean undo() {
        AnnotationData.Annotation undone = annotations.undo();
        if (undone != null) {
            invalidate();
            return true;
        }
        return false;
    }
    
    public boolean redo() {
        AnnotationData.Annotation redone = annotations.redo();
        if (redone != null) {
            invalidate();
            return true;
        }
        return false;
    }
    
    public boolean canUndo() {
        return annotations.canUndo();
    }
    
    public boolean canRedo() {
        return annotations.canRedo();
    }
    
    public void setOnPageChangeListener(OnPageChangeListener listener) {
        this.pageChangeListener = listener;
    }
    
    public void setOnAnnotationListener(OnAnnotationListener listener) {
        this.annotationListener = listener;
    }
    
    public void setOnTextRectListener(OnTextRectListener listener) {
        this.textRectListener = listener;
    }
    
    public void setOnSignatureRectListener(OnSignatureRectListener listener) {
        this.signatureRectListener = listener;
    }
    
    /**
     * Add text annotation at specified PDF point rectangle.
     */
    public void addTextAnnotation(RectF pdfRect, String text, float fontSize) {
        if (pdfRect != null && text != null && !text.isEmpty()) {
            AnnotationData.TextAnnotation textAnn = new AnnotationData.TextAnnotation(
                currentPageIndex, new RectF(pdfRect), text, fontSize, toolColor);
            annotations.add(textAnn);
            invalidate();
            
            if (annotationListener != null) {
                annotationListener.onAnnotationAdded();
            }
        }
    }
    
    /**
     * Add signature annotation at specified PDF point rectangle.
     */
    public void addSignatureAnnotation(String imagePath, RectF pdfRect) {
        if (imagePath != null && pdfRect != null) {
            AnnotationData.SignatureAnnotation sigAnn = new AnnotationData.SignatureAnnotation(
                currentPageIndex, new RectF(pdfRect), imagePath);
            annotations.add(sigAnn);
            invalidate();
            
            if (annotationListener != null) {
                annotationListener.onAnnotationAdded();
            }
        }
    }
    
    /**
     * Clear pending rects (no-op - rects are passed directly to callbacks now).
     */
    public void clearPendingRects() {
        // No-op: pending rects are handled by activity callbacks
    }
    
    public void closePdf() {
        if (currentPage != null) {
            currentPage.close();
            currentPage = null;
        }
        if (pdfRenderer != null) {
            pdfRenderer.close();
            pdfRenderer = null;
        }
        if (fileDescriptor != null) {
            try {
                fileDescriptor.close();
            } catch (Exception e) {
                Log.w(TAG, "Error closing file descriptor: " + e.getMessage());
            }
            fileDescriptor = null;
        }
        if (pageBitmap != null) {
            pageBitmap.recycle();
            pageBitmap = null;
        }
        pageCount = 0;
        currentPageIndex = 0;
    }
    
    // ========== Gesture Listeners ==========
    
    private class ScaleListener extends ScaleGestureDetector.SimpleOnScaleGestureListener {
        @Override
        public boolean onScale(ScaleGestureDetector detector) {
            float scaleFactor = detector.getScaleFactor();
            float newScale = scale * scaleFactor;
            
            if (newScale >= minScale && newScale <= maxScale) {
                float focusX = detector.getFocusX();
                float focusY = detector.getFocusY();
                
                panX = focusX - (focusX - panX) * scaleFactor;
                panY = focusY - (focusY - panY) * scaleFactor;
                scale = newScale;
                
                updateMatrix();
                invalidate();
            }
            
            return true;
        }
        
        @Override
        public boolean onScaleBegin(ScaleGestureDetector detector) {
            isScaling = true;
            return true;
        }
        
        @Override
        public void onScaleEnd(ScaleGestureDetector detector) {
            isScaling = false;
        }
    }
    
    private class GestureListener extends GestureDetector.SimpleOnGestureListener {
        @Override
        public boolean onScroll(MotionEvent e1, MotionEvent e2, float distanceX, float distanceY) {
            if (!isScaling) {
                panX -= distanceX;
                panY -= distanceY;
                updateMatrix();
                invalidate();
            }
            return true;
        }
        
        @Override
        public boolean onDoubleTap(MotionEvent e) {
            fitToScreen();
            invalidate();
            return true;
        }
        
        @Override
        public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
            if (Math.abs(velocityX) > Math.abs(velocityY) && Math.abs(velocityX) > 1000) {
                if (velocityX < 0) {
                    nextPage();
                } else {
                    previousPage();
                }
                return true;
            }
            return false;
        }
    }
}
