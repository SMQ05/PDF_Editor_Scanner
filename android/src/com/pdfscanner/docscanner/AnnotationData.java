package com.pdfscanner.docscanner;

import android.graphics.PointF;
import android.graphics.RectF;

import java.util.ArrayList;
import java.util.List;

/**
 * Data classes for PDF annotations.
 * These are stored in memory during editing and applied on save.
 */
public class AnnotationData {
    
    /**
     * Base class for all annotations.
     */
    public static abstract class Annotation {
        public int pageIndex;
        public long timestamp;
        
        public Annotation(int pageIndex) {
            this.pageIndex = pageIndex;
            this.timestamp = System.currentTimeMillis();
        }
    }
    
    /**
     * Rectangle-based annotation (highlight, underline, strikeout).
     */
    public static class MarkupAnnotation extends Annotation {
        public RectF rect;        // Page coordinates
        public ToolType type;     // HIGHLIGHT, UNDERLINE, STRIKEOUT
        public int color;         // ARGB color
        
        public MarkupAnnotation(int pageIndex, RectF rect, ToolType type, int color) {
            super(pageIndex);
            this.rect = rect;
            this.type = type;
            this.color = color;
        }
    }
    
    /**
     * Ink annotation (pen strokes).
     */
    public static class InkAnnotation extends Annotation {
        public List<List<PointF>> strokes;  // Multiple strokes, each a list of points
        public int color;
        public float strokeWidth;
        
        public InkAnnotation(int pageIndex, int color, float strokeWidth) {
            super(pageIndex);
            this.strokes = new ArrayList<>();
            this.color = color;
            this.strokeWidth = strokeWidth;
        }
        
        public void addStroke(List<PointF> stroke) {
            strokes.add(stroke);
        }
        
        public void startNewStroke() {
            strokes.add(new ArrayList<>());
        }
        
        public void addPoint(PointF point) {
            if (strokes.isEmpty()) {
                startNewStroke();
            }
            strokes.get(strokes.size() - 1).add(point);
        }
    }
    
    /**
     * Redaction annotation (black or white fill).
     */
    public static class RedactionAnnotation extends Annotation {
        public RectF rect;
        public boolean isBlack;   // true=black, false=white
        
        public RedactionAnnotation(int pageIndex, RectF rect, boolean isBlack) {
            super(pageIndex);
            this.rect = rect;
            this.isBlack = isBlack;
        }
    }
    
    /**
     * Text box annotation.
     */
    public static class TextAnnotation extends Annotation {
        public RectF rect;
        public String text;
        public float fontSize;
        public int color;
        public String fontName;
        
        public TextAnnotation(int pageIndex, RectF rect, String text, float fontSize, int color) {
            super(pageIndex);
            this.rect = rect;
            this.text = text;
            this.fontSize = fontSize;
            this.color = color;
            this.fontName = "Helvetica";
        }
    }
    
    /**
     * Signature annotation (image placed on page).
     */
    public static class SignatureAnnotation extends Annotation {
        public RectF rect;
        public String imagePath;   // Path to signature PNG
        
        public SignatureAnnotation(int pageIndex, RectF rect, String imagePath) {
            super(pageIndex);
            this.rect = rect;
            this.imagePath = imagePath;
        }
    }
    
    /**
     * Container for all annotations in a document.
     * Supports undo/redo for annotation history.
     */
    public static class DocumentAnnotations {
        private List<Annotation> annotations = new ArrayList<>();
        private List<Annotation> redoStack = new ArrayList<>();  // Holds undone annotations for redo
        
        /**
         * Add a new annotation. Clears redo stack.
         */
        public void add(Annotation annotation) {
            annotations.add(annotation);
            redoStack.clear();  // Clear redo stack on new action
        }
        
        /**
         * Undo last annotation - moves it to redo stack.
         */
        public Annotation undo() {
            if (annotations.isEmpty()) return null;
            Annotation last = annotations.remove(annotations.size() - 1);
            redoStack.add(last);
            return last;
        }
        
        /**
         * Redo last undone annotation - moves it back to annotations.
         */
        public Annotation redo() {
            if (redoStack.isEmpty()) return null;
            Annotation last = redoStack.remove(redoStack.size() - 1);
            annotations.add(last);
            return last;
        }
        
        public boolean canUndo() {
            return !annotations.isEmpty();
        }
        
        public boolean canRedo() {
            return !redoStack.isEmpty();
        }
        
        public List<Annotation> getAnnotationsForPage(int pageIndex) {
            List<Annotation> result = new ArrayList<>();
            for (Annotation a : annotations) {
                if (a.pageIndex == pageIndex) {
                    result.add(a);
                }
            }
            return result;
        }
        
        public List<Annotation> getAllAnnotations() {
            return new ArrayList<>(annotations);
        }
        
        public void clear() {
            annotations.clear();
            redoStack.clear();
        }
        
        public int size() {
            return annotations.size();
        }
    }
}
