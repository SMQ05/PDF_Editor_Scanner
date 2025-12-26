package com.pdfscanner.docscanner;

import android.os.Bundle;
import android.util.Log;

import org.kivy.android.PythonActivity;

/**
 * Bridge Activity for PDF Scanner app.
 * Extends PythonActivity to provide lifecycle hooks for native components.
 */
public class BridgeActivity extends PythonActivity {
    private static final String TAG = "BridgeActivity";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "BridgeActivity onCreate");
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        Log.d(TAG, "BridgeActivity onResume");
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        Log.d(TAG, "BridgeActivity onPause");
    }
    
    @Override
    protected void onDestroy() {
        // Clean up native resources
        try {
            AdMobManager.destroy();
            BillingManager.destroy();
        } catch (Exception e) {
            Log.e(TAG, "Error cleaning up: " + e.getMessage());
        }
        
        super.onDestroy();
        Log.d(TAG, "BridgeActivity onDestroy");
    }
}
