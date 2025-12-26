package com.pdfscanner.docscanner;

import android.app.Activity;
import android.content.ClipData;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.provider.Settings;
import android.util.Log;

import androidx.core.content.FileProvider;

import java.io.File;

/**
 * Intent utilities for the PDF Scanner app.
 * Handles file sharing and settings navigation.
 */
public class IntentUtils {
    private static final String TAG = "IntentUtils";
    
    /**
     * Share a file using Android's share sheet.
     * Uses FileProvider for secure file sharing.
     * 
     * @param activity The current activity
     * @param filePath Absolute path to the file
     * @param mimeType MIME type of the file
     * @param title Title for the share chooser
     */
    public static void shareFile(Activity activity, String filePath, 
                                  String mimeType, String title) {
        try {
            File file = new File(filePath);
            if (!file.exists()) {
                Log.e(TAG, "File not found: " + filePath);
                return;
            }
            
            // Use Activity context for FileProvider
            String authority = activity.getPackageName() + ".fileprovider";
            
            Uri contentUri = FileProvider.getUriForFile(activity, authority, file);
            
            Intent shareIntent = new Intent(Intent.ACTION_SEND);
            shareIntent.setType(mimeType);
            shareIntent.putExtra(Intent.EXTRA_STREAM, contentUri);
            
            // Add ClipData for maximum compatibility with receiving apps
            shareIntent.setClipData(ClipData.newRawUri("file", contentUri));
            
            // Grant read permission to receiving app
            shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            
            Intent chooser = Intent.createChooser(shareIntent, title);
            activity.startActivity(chooser);
            
            Log.d(TAG, "Share intent launched for: " + filePath);
        } catch (IllegalArgumentException e) {
            Log.e(TAG, "FileProvider configuration error: " + e.getMessage());
            Log.e(TAG, "Check that file_paths.xml covers the directory containing: " + filePath);
        } catch (Exception e) {
            Log.e(TAG, "Failed to share file: " + e.getMessage());
        }
    }
    
    /**
     * Open the app's settings screen.
     * Used for permission recovery when user selected "Don't ask again".
     * 
     * @param activity The current activity
     */
    public static void openAppSettings(Activity activity) {
        try {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            Uri uri = Uri.fromParts("package", activity.getPackageName(), null);
            intent.setData(uri);
            activity.startActivity(intent);
            
            Log.d(TAG, "Opened app settings");
        } catch (Exception e) {
            Log.e(TAG, "Failed to open settings: " + e.getMessage());
        }
    }
    
    /**
     * Open a URL in the default browser.
     * 
     * @param activity The current activity
     * @param url URL to open
     */
    public static void openUrl(Activity activity, String url) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setData(Uri.parse(url));
            activity.startActivity(intent);
            
            Log.d(TAG, "Opened URL: " + url);
        } catch (Exception e) {
            Log.e(TAG, "Failed to open URL: " + e.getMessage());
        }
    }
    
    /**
     * Get content URI for a file using FileProvider.
     * 
     * @param activity Activity context (preferred over application context)
     * @param filePath Absolute path to the file
     * @return Content URI or null on error
     */
    public static Uri getContentUri(Activity activity, String filePath) {
        try {
            File file = new File(filePath);
            String authority = activity.getPackageName() + ".fileprovider";
            return FileProvider.getUriForFile(activity, authority, file);
        } catch (IllegalArgumentException e) {
            Log.e(TAG, "FileProvider error - check file_paths.xml: " + e.getMessage());
            return null;
        } catch (Exception e) {
            Log.e(TAG, "Failed to get content URI: " + e.getMessage());
            return null;
        }
    }
}
