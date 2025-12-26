package com.pdfscanner.docscanner;

import android.graphics.Color;
import android.graphics.PointF;
import android.graphics.RectF;
import android.util.Log;

import com.tom_roush.pdfbox.android.PDFBoxResourceLoader;
import com.tom_roush.pdfbox.pdmodel.PDDocument;
import com.tom_roush.pdfbox.pdmodel.PDPage;
import com.tom_roush.pdfbox.pdmodel.PDPageContentStream;
import com.tom_roush.pdfbox.pdmodel.common.PDRectangle;
import com.tom_roush.pdfbox.pdmodel.font.PDType1Font;
import com.tom_roush.pdfbox.pdmodel.graphics.image.PDImageXObject;
import com.tom_roush.pdfbox.pdmodel.interactive.annotation.PDAnnotationTextMarkup;

import java.io.File;
import java.util.List;

/**
 * PDF editing engine using PDFBox-Android.
 * Handles adding annotations, redactions, text, and signatures to PDFs.
 * 
 * COORDINATE SYSTEM:
 * - Expects all input coordinates (AnnotationData) in PDF POINTS (72 DPI)
 * - Origin: Top-left (Android convention)
 * - Converts to PDFBox bottom-left origin internally
 * 
 * IMPORTANT: Saving is stateless - we load a fresh doc each save to avoid
 * duplicating annotations on repeated saves.
 */
public class PdfEditEngine {
    private static final String TAG = "PdfEditEngine";
    
    private android.content.Context context;
    private String originalFilePath;  // Store for stateless saves
    private boolean isInitialized = false;
    
    public PdfEditEngine(android.content.Context context) {
        this.context = context;
        
        try {
            PDFBoxResourceLoader.init(context);
            isInitialized = true;
            Log.d(TAG, "PDFBox initialized successfully");
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize PDFBox: " + e.getMessage());
        }
    }
    
    /**
     * Set the source PDF file path for editing.
     * 
     * @param filePath Path to the PDF file
     * @return true if file exists and is readable
     */
    public boolean loadDocument(String filePath) {
        if (!isInitialized) {
            Log.e(TAG, "PDFBox not initialized");
            return false;
        }
        
        File file = new File(filePath);
        if (!file.exists()) {
            Log.e(TAG, "File not found: " + filePath);
            return false;
        }
        
        // Check if encrypted
        if (isEncrypted(filePath)) {
            Log.e(TAG, "Document is encrypted");
            return false;
        }
        
        originalFilePath = filePath;
        Log.d(TAG, "Set source document: " + filePath);
        return true;
    }
    
    /**
     * Check if document is encrypted.
     */
    public boolean isEncrypted(String filePath) {
        PDDocument doc = null;
        try {
            File file = new File(filePath);
            doc = PDDocument.load(file);
            boolean encrypted = doc.isEncrypted();
            return encrypted;
        } catch (Exception e) {
            return true;  // Assume encrypted on error
        } finally {
            if (doc != null) {
                try { doc.close(); } catch (Exception e) {}
            }
        }
    }
    
    /**
     * Get the number of pages in the source document.
     */
    public int getPageCount() {
        if (originalFilePath == null) return 0;
        
        PDDocument doc = null;
        try {
            doc = PDDocument.load(new File(originalFilePath));
            return doc.getNumberOfPages();
        } catch (Exception e) {
            return 0;
        } finally {
            if (doc != null) {
                try { doc.close(); } catch (Exception e) {}
            }
        }
    }
    
    /**
     * Save document with annotations to a new file.
     * 
     * STATELESS: Opens a fresh copy of original, applies annotations, saves.
     * This prevents annotation duplication on repeated saves.
     * 
     * @param annotations Annotations to apply
     * @param outputPath Path for the output file
     * @return true if saved successfully
     */
    public boolean saveWithAnnotations(AnnotationData.DocumentAnnotations annotations, 
                                        String outputPath) {
        if (originalFilePath == null) {
            Log.e(TAG, "No source document set");
            return false;
        }
        
        PDDocument document = null;
        try {
            // Load a FRESH copy of the original document
            document = PDDocument.load(new File(originalFilePath));
            
            if (document.isEncrypted()) {
                Log.e(TAG, "Cannot save encrypted document");
                return false;
            }
            
            // Apply all annotations to the fresh copy
            applyAnnotationsToDocument(document, annotations);
            
            // Ensure output directory exists
            File outputFile = new File(outputPath);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }
            
            // Save
            document.save(outputFile);
            Log.d(TAG, "Saved document to: " + outputPath);
            return true;
            
        } catch (Exception e) {
            Log.e(TAG, "Failed to save document: " + e.getMessage());
            return false;
        } finally {
            if (document != null) {
                try { document.close(); } catch (Exception e) {}
            }
        }
    }
    
    /**
     * Legacy method for compatibility - calls saveWithAnnotations.
     */
    public boolean applyAnnotations(AnnotationData.DocumentAnnotations annotations) {
        // This method is now a no-op - use saveWithAnnotations instead
        Log.w(TAG, "applyAnnotations called - use saveWithAnnotations for proper save");
        return true;
    }
    
    /**
     * Legacy saveAs - now uses stateless save.
     */
    public boolean saveAs(String outputPath) {
        Log.w(TAG, "saveAs without annotations - saving original copy");
        if (originalFilePath == null) return false;
        
        PDDocument document = null;
        try {
            document = PDDocument.load(new File(originalFilePath));
            File outputFile = new File(outputPath);
            File parentDir = outputFile.getParentFile();
            if (parentDir != null && !parentDir.exists()) {
                parentDir.mkdirs();
            }
            document.save(outputFile);
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to save: " + e.getMessage());
            return false;
        } finally {
            if (document != null) {
                try { document.close(); } catch (Exception e) {}
            }
        }
    }
    
    /**
     * Apply all annotations to a document.
     */
    private void applyAnnotationsToDocument(PDDocument document, 
                                             AnnotationData.DocumentAnnotations annotations) {
        if (annotations == null) return;
        
        for (AnnotationData.Annotation ann : annotations.getAllAnnotations()) {
            try {
                if (ann instanceof AnnotationData.MarkupAnnotation) {
                    applyMarkup(document, (AnnotationData.MarkupAnnotation) ann);
                } else if (ann instanceof AnnotationData.InkAnnotation) {
                    applyInk(document, (AnnotationData.InkAnnotation) ann);
                } else if (ann instanceof AnnotationData.RedactionAnnotation) {
                    applyRedaction(document, (AnnotationData.RedactionAnnotation) ann);
                } else if (ann instanceof AnnotationData.TextAnnotation) {
                    applyText(document, (AnnotationData.TextAnnotation) ann);
                } else if (ann instanceof AnnotationData.SignatureAnnotation) {
                    applySignature(document, (AnnotationData.SignatureAnnotation) ann);
                }
            } catch (Exception e) {
                Log.e(TAG, "Failed to apply annotation: " + e.getMessage());
            }
        }
    }
    
    private void applyMarkup(PDDocument document, AnnotationData.MarkupAnnotation markup) 
            throws Exception {
        if (markup.pageIndex >= document.getNumberOfPages()) return;
        
        PDPage page = document.getPage(markup.pageIndex);
        PDRectangle pageRect = page.getMediaBox();
        
        // Convert to PDF coordinates (origin bottom-left)
        float pdfY1 = pageRect.getHeight() - markup.rect.bottom;
        float pdfY2 = pageRect.getHeight() - markup.rect.top;
        
        String subtype;
        switch (markup.type) {
            case UNDERLINE:
                subtype = PDAnnotationTextMarkup.SUB_TYPE_UNDERLINE;
                break;
            case STRIKEOUT:
                subtype = PDAnnotationTextMarkup.SUB_TYPE_STRIKEOUT;
                break;
            default:
                subtype = PDAnnotationTextMarkup.SUB_TYPE_HIGHLIGHT;
        }
        
        PDAnnotationTextMarkup annotation = new PDAnnotationTextMarkup(subtype);
        
        PDRectangle annotRect = new PDRectangle(markup.rect.left, pdfY1, 
            markup.rect.width(), markup.rect.height());
        annotation.setRectangle(annotRect);
        
        float[] quads = new float[] {
            markup.rect.left, pdfY2, markup.rect.right, pdfY2,
            markup.rect.left, pdfY1, markup.rect.right, pdfY1
        };
        annotation.setQuadPoints(quads);
        
        float[] colorArray = colorToFloatArray(markup.color);
        annotation.setColor(new com.tom_roush.pdfbox.pdmodel.graphics.color.PDColor(
            colorArray, com.tom_roush.pdfbox.pdmodel.graphics.color.PDDeviceRGB.INSTANCE));
        
        page.getAnnotations().add(annotation);
    }
    
    private void applyRedaction(PDDocument document, AnnotationData.RedactionAnnotation redact) 
            throws Exception {
        if (redact.pageIndex >= document.getNumberOfPages()) return;
        
        PDPage page = document.getPage(redact.pageIndex);
        PDRectangle pageRect = page.getMediaBox();
        
        float pdfY = pageRect.getHeight() - redact.rect.bottom;
        
        PDPageContentStream contentStream = new PDPageContentStream(
            document, page, PDPageContentStream.AppendMode.APPEND, true, true);
        
        if (redact.isBlack) {
            contentStream.setNonStrokingColor(0f, 0f, 0f);
        } else {
            contentStream.setNonStrokingColor(1f, 1f, 1f);
        }
        
        contentStream.addRect(redact.rect.left, pdfY, redact.rect.width(), redact.rect.height());
        contentStream.fill();
        contentStream.close();
    }
    
    private void applyInk(PDDocument document, AnnotationData.InkAnnotation ink) 
            throws Exception {
        if (ink.pageIndex >= document.getNumberOfPages()) return;
        if (ink.strokes == null || ink.strokes.isEmpty()) return;
        
        PDPage page = document.getPage(ink.pageIndex);
        PDRectangle pageRect = page.getMediaBox();
        
        PDPageContentStream contentStream = new PDPageContentStream(
            document, page, PDPageContentStream.AppendMode.APPEND, true, true);
        
        float[] colorArray = colorToFloatArray(ink.color);
        contentStream.setStrokingColor(colorArray[0], colorArray[1], colorArray[2]);
        contentStream.setLineWidth(ink.strokeWidth);
        contentStream.setLineCapStyle(1);
        contentStream.setLineJoinStyle(1);
        
        for (List<PointF> stroke : ink.strokes) {
            if (stroke.size() < 2) continue;
            
            PointF first = stroke.get(0);
            float pdfY = pageRect.getHeight() - first.y;
            contentStream.moveTo(first.x, pdfY);
            
            for (int i = 1; i < stroke.size(); i++) {
                PointF pt = stroke.get(i);
                pdfY = pageRect.getHeight() - pt.y;
                contentStream.lineTo(pt.x, pdfY);
            }
            
            contentStream.stroke();
        }
        
        contentStream.close();
    }
    
    private void applyText(PDDocument document, AnnotationData.TextAnnotation text) 
            throws Exception {
        if (text.pageIndex >= document.getNumberOfPages()) return;
        if (text.text == null || text.text.isEmpty()) return;
        
        PDPage page = document.getPage(text.pageIndex);
        PDRectangle pageRect = page.getMediaBox();
        
        float pdfY = pageRect.getHeight() - text.rect.top - text.fontSize;
        
        PDPageContentStream contentStream = new PDPageContentStream(
            document, page, PDPageContentStream.AppendMode.APPEND, true, true);
        
        float[] colorArray = colorToFloatArray(text.color);
        contentStream.setNonStrokingColor(colorArray[0], colorArray[1], colorArray[2]);
        contentStream.setFont(PDType1Font.HELVETICA, text.fontSize);
        
        contentStream.beginText();
        contentStream.newLineAtOffset(text.rect.left, pdfY);
        contentStream.showText(text.text);
        contentStream.endText();
        
        contentStream.close();
    }
    
    private void applySignature(PDDocument document, AnnotationData.SignatureAnnotation sig) 
            throws Exception {
        if (sig.pageIndex >= document.getNumberOfPages()) return;
        if (sig.imagePath == null) return;
        
        File imageFile = new File(sig.imagePath);
        if (!imageFile.exists()) {
            Log.e(TAG, "Signature image not found: " + sig.imagePath);
            return;
        }
        
        PDPage page = document.getPage(sig.pageIndex);
        PDRectangle pageRect = page.getMediaBox();
        
        PDImageXObject image = PDImageXObject.createFromFile(sig.imagePath, document);
        
        float pdfY = pageRect.getHeight() - sig.rect.bottom;
        
        PDPageContentStream contentStream = new PDPageContentStream(
            document, page, PDPageContentStream.AppendMode.APPEND, true, true);
        
        contentStream.drawImage(image, sig.rect.left, pdfY, sig.rect.width(), sig.rect.height());
        contentStream.close();
    }
    
    private float[] colorToFloatArray(int color) {
        return new float[] {
            Color.red(color) / 255f,
            Color.green(color) / 255f,
            Color.blue(color) / 255f
        };
    }
    
    public void closeDocument() {
        // Nothing to close - we use stateless saves now
        originalFilePath = null;
    }
    
    public String getCurrentFilePath() {
        return originalFilePath;
    }
    
    public boolean isDocumentLoaded() {
        return originalFilePath != null;
    }
}
