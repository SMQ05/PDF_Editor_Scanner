package com.pdfscanner.docscanner;

import android.app.Activity;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.util.Log;

import com.google.android.gms.ads.AdListener;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.AdSize;
import com.google.android.gms.ads.AdView;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.interstitial.InterstitialAd;
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback;

/**
 * Manages AdMob ads for the PDF Scanner app.
 * Provides static methods callable from Python via PyJNIus.
 */
public class AdMobManager {
    private static final String TAG = "AdMobManager";
    
    private static boolean isInitialized = false;
    private static AdView bannerAdView = null;
    private static InterstitialAd interstitialAd = null;
    private static boolean wasInterstitialClosed = false;
    private static LinearLayout adContainer = null;
    
    /**
     * Initialize AdMob SDK.
     * Must be called before using any other methods.
     */
    public static void initialize(final Activity activity) {
        if (isInitialized) {
            Log.d(TAG, "Already initialized");
            return;
        }
        
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    MobileAds.initialize(activity, initializationStatus -> {
                        Log.d(TAG, "AdMob SDK initialized");
                        isInitialized = true;
                    });
                } catch (Exception e) {
                    Log.e(TAG, "Failed to initialize AdMob: " + e.getMessage());
                }
            }
        });
    }
    
    /**
     * Show banner ad at the bottom of the screen.
     */
    public static void showBanner(final Activity activity, final String adUnitId) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    // Create container if needed
                    if (adContainer == null) {
                        adContainer = new LinearLayout(activity);
                        adContainer.setOrientation(LinearLayout.VERTICAL);
                        adContainer.setGravity(Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
                        
                        FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                            FrameLayout.LayoutParams.MATCH_PARENT,
                            FrameLayout.LayoutParams.WRAP_CONTENT
                        );
                        params.gravity = Gravity.BOTTOM;
                        
                        ViewGroup rootView = activity.findViewById(android.R.id.content);
                        rootView.addView(adContainer, params);
                    }
                    
                    // Create banner ad if needed
                    if (bannerAdView == null) {
                        bannerAdView = new AdView(activity);
                        bannerAdView.setAdSize(AdSize.BANNER);
                        bannerAdView.setAdUnitId(adUnitId);
                        
                        bannerAdView.setAdListener(new AdListener() {
                            @Override
                            public void onAdLoaded() {
                                Log.d(TAG, "Banner ad loaded");
                            }
                            
                            @Override
                            public void onAdFailedToLoad(LoadAdError error) {
                                Log.e(TAG, "Banner ad failed to load: " + error.getMessage());
                            }
                        });
                        
                        adContainer.addView(bannerAdView);
                    }
                    
                    // Load and show
                    AdRequest adRequest = new AdRequest.Builder().build();
                    bannerAdView.loadAd(adRequest);
                    adContainer.setVisibility(View.VISIBLE);
                    
                    Log.d(TAG, "Banner shown");
                } catch (Exception e) {
                    Log.e(TAG, "Failed to show banner: " + e.getMessage());
                }
            }
        });
    }
    
    /**
     * Hide the banner ad.
     */
    public static void hideBanner() {
        if (adContainer != null) {
            adContainer.post(new Runnable() {
                @Override
                public void run() {
                    adContainer.setVisibility(View.GONE);
                    Log.d(TAG, "Banner hidden");
                }
            });
        }
    }
    
    /**
     * Load an interstitial ad.
     */
    public static void loadInterstitial(final Activity activity, final String adUnitId) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    AdRequest adRequest = new AdRequest.Builder().build();
                    
                    InterstitialAd.load(activity, adUnitId, adRequest,
                        new InterstitialAdLoadCallback() {
                            @Override
                            public void onAdLoaded(InterstitialAd ad) {
                                interstitialAd = ad;
                                wasInterstitialClosed = false;
                                Log.d(TAG, "Interstitial loaded");
                                
                                // Set callback for when ad is shown
                                ad.setFullScreenContentCallback(new FullScreenContentCallback() {
                                    @Override
                                    public void onAdDismissedFullScreenContent() {
                                        wasInterstitialClosed = true;
                                        interstitialAd = null;
                                        Log.d(TAG, "Interstitial closed");
                                    }
                                    
                                    @Override
                                    public void onAdFailedToShowFullScreenContent(
                                            com.google.android.gms.ads.AdError error) {
                                        wasInterstitialClosed = true;
                                        interstitialAd = null;
                                        Log.e(TAG, "Interstitial failed to show: " + error.getMessage());
                                    }
                                });
                            }
                            
                            @Override
                            public void onAdFailedToLoad(LoadAdError error) {
                                interstitialAd = null;
                                Log.e(TAG, "Interstitial failed to load: " + error.getMessage());
                            }
                        });
                } catch (Exception e) {
                    Log.e(TAG, "Failed to load interstitial: " + e.getMessage());
                }
            }
        });
    }
    
    /**
     * Check if an interstitial ad is ready to show.
     */
    public static boolean isInterstitialReady() {
        return interstitialAd != null;
    }
    
    /**
     * Show the loaded interstitial ad.
     */
    public static void showInterstitial(final Activity activity) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (interstitialAd != null) {
                    wasInterstitialClosed = false;
                    interstitialAd.show(activity);
                    Log.d(TAG, "Interstitial shown");
                } else {
                    Log.d(TAG, "No interstitial to show");
                    wasInterstitialClosed = true;
                }
            }
        });
    }
    
    /**
     * Check if interstitial was closed (used for callback polling).
     */
    public static boolean wasInterstitialClosed() {
        return wasInterstitialClosed;
    }
    
    /**
     * Clean up resources.
     */
    public static void destroy() {
        if (bannerAdView != null) {
            bannerAdView.destroy();
            bannerAdView = null;
        }
        interstitialAd = null;
        adContainer = null;
        Log.d(TAG, "AdMob resources destroyed");
    }
}
