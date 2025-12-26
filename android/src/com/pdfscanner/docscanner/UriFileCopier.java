package com.pdfscanner.docscanner;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Utility to copy content URIs to app-private storage.
 * Required for handling PDFs opened from file manager or other apps.
 */
public class UriFileCopier {
    private static final String TAG = "UriFileCopier";
    private static final int BUFFER_SIZE = 8192;
    
    /**
     * Copy a content URI to app-private storage.
     * 
     * @param context Application context
     * @param contentUri Content URI to copy
     * @param destinationDir Destination directory in app storage
     * @param suggestedName Suggested filename (may be null)
     * @return Path to copied file, or null on failure
     */
    public static String copyToPrivateStorage(Context context, Uri contentUri,
                                               File destinationDir, String suggestedName) {
        if (contentUri == null) {
            Log.e(TAG, "Content URI is null");
            return null;
        }
        
        if (destinationDir == null) {
            Log.e(TAG, "Destination directory is null");
            return null;
        }
        
        // Ensure destination directory exists
        if (!destinationDir.exists()) {
            boolean created = destinationDir.mkdirs();
            if (!created && !destinationDir.exists()) {
                Log.e(TAG, "Failed to create destination directory: " + destinationDir);
                return null;
            }
        }
        
        // Use try-with-resources for guaranteed stream closure
        try (InputStream inputStream = context.getContentResolver().openInputStream(contentUri)) {
            
            if (inputStream == null) {
                Log.e(TAG, "Failed to open input stream for: " + contentUri);
                return null;
            }
            
            // Generate filename
            String filename = suggestedName;
            if (filename == null || filename.isEmpty()) {
                filename = getFileNameFromUri(context, contentUri);
            }
            if (filename == null || filename.isEmpty()) {
                filename = "imported_" + System.currentTimeMillis() + ".pdf";
            }
            
            // Sanitize filename - remove path separators
            filename = sanitizeFilename(filename);
            
            // Ensure .pdf extension
            if (!filename.toLowerCase().endsWith(".pdf")) {
                filename += ".pdf";
            }
            
            // Create unique filename if exists
            File destinationFile = new File(destinationDir, filename);
            int counter = 1;
            while (destinationFile.exists()) {
                String baseName = filename.substring(0, filename.length() - 4);
                destinationFile = new File(destinationDir, baseName + "_" + counter + ".pdf");
                counter++;
            }
            
            // Copy file using try-with-resources for output
            try (OutputStream outputStream = new FileOutputStream(destinationFile)) {
                byte[] buffer = new byte[BUFFER_SIZE];
                int bytesRead;
                
                while ((bytesRead = inputStream.read(buffer)) != -1) {
                    outputStream.write(buffer, 0, bytesRead);
                }
                
                outputStream.flush();
            }
            
            Log.d(TAG, "Copied URI to: " + destinationFile.getAbsolutePath());
            return destinationFile.getAbsolutePath();
            
        } catch (Exception e) {
            Log.e(TAG, "Failed to copy URI: " + e.getMessage());
            return null;
        }
    }
    
    /**
     * Sanitize filename to remove path separators and invalid characters.
     */
    private static String sanitizeFilename(String filename) {
        if (filename == null) return null;
        
        // Remove path separators
        filename = filename.replace("/", "_");
        filename = filename.replace("\\", "_");
        filename = filename.replace(":", "_");
        
        // Remove other problematic characters
        filename = filename.replace("*", "_");
        filename = filename.replace("?", "_");
        filename = filename.replace("\"", "_");
        filename = filename.replace("<", "_");
        filename = filename.replace(">", "_");
        filename = filename.replace("|", "_");
        
        return filename.trim();
    }
    
    /**
     * Try to extract filename from content URI using OpenableColumns.
     */
    private static String getFileNameFromUri(Context context, Uri uri) {
        String result = null;
        
        try {
            if ("content".equals(uri.getScheme())) {
                try (Cursor cursor = context.getContentResolver()
                        .query(uri, null, null, null, null)) {
                    
                    if (cursor != null && cursor.moveToFirst()) {
                        int nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                        if (nameIndex >= 0) {
                            result = cursor.getString(nameIndex);
                        }
                    }
                }
            }
            
            if (result == null) {
                result = uri.getLastPathSegment();
            }
        } catch (Exception e) {
            Log.w(TAG, "Could not get filename from URI: " + e.getMessage());
        }
        
        return result;
    }
    
    /**
     * Check if a URI is a file URI vs content URI.
     */
    public static boolean isFileUri(Uri uri) {
        return uri != null && "file".equals(uri.getScheme());
    }
    
    /**
     * Get file path from file URI.
     */
    public static String getPathFromFileUri(Uri uri) {
        if (isFileUri(uri)) {
            return uri.getPath();
        }
        return null;
    }
}
