package com.pdfscanner.docscanner;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.View;

import java.io.File;
import java.io.FileOutputStream;

/**
 * Touch-based signature capture view.
 * Captures user's signature and exports as transparent PNG.
 */
public class SignaturePadView extends View {
    private static final String TAG = "SignaturePadView";
    
    private Paint paint;
    private Path path;
    private Bitmap bitmap;
    private Canvas bitmapCanvas;
    
    private float lastX, lastY;
    private boolean hasSignature = false;
    
    // Configurable
    private int strokeColor = Color.BLACK;
    private float strokeWidth = 5f;
    private int backgroundColor = Color.TRANSPARENT;
    
    public SignaturePadView(Context context) {
        super(context);
        init();
    }
    
    public SignaturePadView(Context context, AttributeSet attrs) {
        super(context, attrs);
        init();
    }
    
    public SignaturePadView(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        init();
    }
    
    private void init() {
        paint = new Paint();
        paint.setColor(strokeColor);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(strokeWidth);
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStrokeJoin(Paint.Join.ROUND);
        paint.setAntiAlias(true);
        
        path = new Path();
    }
    
    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        
        if (w > 0 && h > 0) {
            bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            bitmapCanvas = new Canvas(bitmap);
            bitmapCanvas.drawColor(backgroundColor);
        }
    }
    
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        
        if (bitmap != null) {
            canvas.drawBitmap(bitmap, 0, 0, null);
        }
        canvas.drawPath(path, paint);
    }
    
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        float x = event.getX();
        float y = event.getY();
        
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                path.moveTo(x, y);
                lastX = x;
                lastY = y;
                hasSignature = true;
                return true;
                
            case MotionEvent.ACTION_MOVE:
                path.quadTo(lastX, lastY, (x + lastX) / 2, (y + lastY) / 2);
                lastX = x;
                lastY = y;
                break;
                
            case MotionEvent.ACTION_UP:
                path.lineTo(x, y);
                // Draw path to bitmap
                if (bitmapCanvas != null) {
                    bitmapCanvas.drawPath(path, paint);
                }
                path.reset();
                break;
                
            default:
                return false;
        }
        
        invalidate();
        return true;
    }
    
    /**
     * Clear the signature.
     */
    public void clear() {
        path.reset();
        if (bitmap != null) {
            bitmap.eraseColor(backgroundColor);
        }
        hasSignature = false;
        invalidate();
    }
    
    /**
     * Check if user has drawn a signature.
     */
    public boolean hasSignature() {
        return hasSignature;
    }
    
    /**
     * Export signature as transparent PNG.
     * 
     * @param outputPath Path to save the PNG file
     * @return true if successful
     */
    public boolean exportToPng(String outputPath) {
        if (bitmap == null || !hasSignature) {
            return false;
        }
        
        try {
            // Get bounds of actual signature (crop whitespace)
            Bitmap cropped = cropSignature();
            if (cropped == null) {
                cropped = bitmap;
            }
            
            FileOutputStream fos = new FileOutputStream(new File(outputPath));
            cropped.compress(Bitmap.CompressFormat.PNG, 100, fos);
            fos.flush();
            fos.close();
            
            if (cropped != bitmap) {
                cropped.recycle();
            }
            
            return true;
        } catch (Exception e) {
            android.util.Log.e(TAG, "Failed to export signature: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * Crop the signature bitmap to remove excess transparent space.
     */
    private Bitmap cropSignature() {
        if (bitmap == null) return null;
        
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        
        int minX = width, maxX = 0;
        int minY = height, maxY = 0;
        
        // Find bounds of non-transparent pixels
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int pixel = bitmap.getPixel(x, y);
                if (Color.alpha(pixel) > 0) {
                    minX = Math.min(minX, x);
                    maxX = Math.max(maxX, x);
                    minY = Math.min(minY, y);
                    maxY = Math.max(maxY, y);
                }
            }
        }
        
        if (minX >= maxX || minY >= maxY) {
            return null;  // No visible content
        }
        
        // Add padding
        int padding = 10;
        minX = Math.max(0, minX - padding);
        minY = Math.max(0, minY - padding);
        maxX = Math.min(width - 1, maxX + padding);
        maxY = Math.min(height - 1, maxY + padding);
        
        return Bitmap.createBitmap(bitmap, minX, minY, maxX - minX + 1, maxY - minY + 1);
    }
    
    /**
     * Get the signature bitmap directly.
     */
    public Bitmap getSignatureBitmap() {
        return bitmap;
    }
    
    /**
     * Set stroke color.
     */
    public void setStrokeColor(int color) {
        this.strokeColor = color;
        paint.setColor(color);
    }
    
    /**
     * Set stroke width.
     */
    public void setStrokeWidth(float width) {
        this.strokeWidth = width;
        paint.setStrokeWidth(width);
    }
}
