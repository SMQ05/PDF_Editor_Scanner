package com.pdfscanner.docscanner;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;

import java.io.File;

/**
 * Lightweight activity to handle "Open with..." for PDF files.
 * 
 * Flow:
 * 1. Receives ACTION_VIEW intent with PDF content URI
 * 2. Takes persistable URI permission when available
 * 3. Copies the file to app-private storage via ContentResolver
 * 4. Launches PdfViewerActivity with the local file path
 * 5. Finishes immediately
 */
public class PdfOpenActivity extends Activity {
    private static final String TAG = "PdfOpenActivity";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        Intent intent = getIntent();
        String action = intent.getAction();
        
        if (Intent.ACTION_VIEW.equals(action)) {
            handleViewIntent(intent);
        } else {
            Log.e(TAG, "Unexpected action: " + action);
            finish();
        }
    }
    
    private void handleViewIntent(Intent intent) {
        Uri uri = intent.getData();
        
        if (uri == null) {
            Log.e(TAG, "No URI in intent");
            Toast.makeText(this, "No file specified", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        Log.d(TAG, "Received URI: " + uri.toString());
        
        // Take persistable URI permission if available
        takePersistablePermission(intent, uri);
        
        // Copy to private storage
        String filePath = null;
        try {
            filePath = copyUriToPrivateStorage(uri);
        } catch (Exception e) {
            Log.e(TAG, "Failed to copy URI: " + e.getMessage());
            Toast.makeText(this, "Failed to open PDF file", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        if (filePath == null) {
            Toast.makeText(this, "Failed to read PDF file", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        // Verify file exists and has content
        File file = new File(filePath);
        if (!file.exists() || file.length() == 0) {
            Log.e(TAG, "Copied file invalid: " + filePath);
            Toast.makeText(this, "Invalid PDF file", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        Log.d(TAG, "Copied to: " + filePath + " (" + file.length() + " bytes)");
        
        // Launch PDF viewer with CLEAR_TOP for clean stack
        Intent viewerIntent = new Intent(this, PdfViewerActivity.class);
        viewerIntent.putExtra(PdfViewerActivity.EXTRA_PDF_PATH, filePath);
        viewerIntent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(viewerIntent);
        
        // Finish immediately
        finish();
    }
    
    /**
     * Take persistable URI permission if available and flags allow.
     */
    private void takePersistablePermission(Intent intent, Uri uri) {
        try {
            int flags = intent.getFlags();
            
            // Check if persistable permission is offered
            boolean hasPersistable = (flags & Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION) != 0;
            if (!hasPersistable) {
                Log.d(TAG, "No persistable permission offered (temporary access)");
                return;
            }
            
            // Compute which permissions to take
            int takeFlags = flags & (Intent.FLAG_GRANT_READ_URI_PERMISSION 
                                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            
            if (takeFlags == 0) {
                Log.d(TAG, "No read/write flags to take");
                return;
            }
            
            ContentResolver resolver = getContentResolver();
            resolver.takePersistableUriPermission(uri, takeFlags);
            Log.d(TAG, "Took persistable permission with flags: " + takeFlags);
            
        } catch (SecurityException e) {
            // Permission not grantable - okay for temp access
            Log.d(TAG, "Could not take persistable permission: " + e.getMessage());
        } catch (Exception e) {
            Log.w(TAG, "Error taking permission: " + e.getMessage());
        }
    }
    
    /**
     * Copy URI content to app-private storage using ContentResolver.
     */
    private String copyUriToPrivateStorage(Uri uri) {
        File importDir = new File(getFilesDir(), "imported");
        return UriFileCopier.copyToPrivateStorage(this, uri, importDir, null);
    }
}
