package com.pdfscanner.docscanner;

import android.app.Activity;
import android.util.Log;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.ProductDetailsResponseListener;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryPurchasesParams;

import java.util.ArrayList;
import java.util.List;

/**
 * Manages Google Play Billing for the PDF Scanner app.
 * Handles Remove Ads in-app purchase.
 */
public class BillingManager implements PurchasesUpdatedListener {
    private static final String TAG = "BillingManager";
    
    private static BillingManager instance;
    private BillingClient billingClient;
    private boolean isConnected = false;
    private ProductDetails removeAdsProduct = null;
    private String lastPurchaseResult = null;
    private Boolean isRemoveAdsPurchased = null;
    
    private static final String REMOVE_ADS_SKU = "remove_ads";
    
    private BillingManager() {}
    
    /**
     * Get singleton instance.
     */
    public static synchronized BillingManager getInstance() {
        if (instance == null) {
            instance = new BillingManager();
        }
        return instance;
    }
    
    /**
     * Initialize billing client.
     */
    public static void initialize(final Activity activity) {
        BillingManager manager = getInstance();
        manager.initBillingClient(activity);
    }
    
    private void initBillingClient(Activity activity) {
        if (billingClient != null && isConnected) {
            Log.d(TAG, "Already initialized and connected");
            return;
        }
        
        billingClient = BillingClient.newBuilder(activity)
            .setListener(this)
            .enablePendingPurchases()
            .build();
        
        billingClient.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult billingResult) {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    isConnected = true;
                    Log.d(TAG, "Billing client connected");
                    queryProductDetails();
                    queryExistingPurchases();
                } else {
                    Log.e(TAG, "Billing setup failed: " + billingResult.getDebugMessage());
                }
            }
            
            @Override
            public void onBillingServiceDisconnected() {
                isConnected = false;
                Log.d(TAG, "Billing service disconnected");
            }
        });
    }
    
    /**
     * Query product details for Remove Ads.
     */
    private void queryProductDetails() {
        List<QueryProductDetailsParams.Product> productList = new ArrayList<>();
        productList.add(
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId(REMOVE_ADS_SKU)
                .setProductType(BillingClient.ProductType.INAPP)
                .build()
        );
        
        QueryProductDetailsParams params = QueryProductDetailsParams.newBuilder()
            .setProductList(productList)
            .build();
        
        billingClient.queryProductDetailsAsync(params, new ProductDetailsResponseListener() {
            @Override
            public void onProductDetailsResponse(BillingResult billingResult,
                    List<ProductDetails> productDetailsList) {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK
                        && productDetailsList != null && !productDetailsList.isEmpty()) {
                    removeAdsProduct = productDetailsList.get(0);
                    Log.d(TAG, "Product details loaded: " + removeAdsProduct.getName());
                } else {
                    Log.e(TAG, "Failed to load product details");
                }
            }
        });
    }
    
    /**
     * Query existing purchases.
     */
    private void queryExistingPurchases() {
        QueryPurchasesParams params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.INAPP)
            .build();
        
        billingClient.queryPurchasesAsync(params, (billingResult, purchases) -> {
            if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                isRemoveAdsPurchased = false;
                for (Purchase purchase : purchases) {
                    if (purchase.getProducts().contains(REMOVE_ADS_SKU)) {
                        if (purchase.getPurchaseState() == Purchase.PurchaseState.PURCHASED) {
                            isRemoveAdsPurchased = true;
                            acknowledgePurchaseIfNeeded(purchase);
                            Log.d(TAG, "Remove Ads is purchased");
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Acknowledge a purchase if not already acknowledged.
     */
    private void acknowledgePurchaseIfNeeded(Purchase purchase) {
        if (!purchase.isAcknowledged()) {
            AcknowledgePurchaseParams params = AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(purchase.getPurchaseToken())
                .build();
            
            billingClient.acknowledgePurchase(params, billingResult -> {
                if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    Log.d(TAG, "Purchase acknowledged");
                }
            });
        }
    }
    
    /**
     * Start purchase flow for Remove Ads.
     */
    public static void purchaseRemoveAds(Activity activity, String sku) {
        BillingManager manager = getInstance();
        manager.launchPurchaseFlow(activity);
    }
    
    private void launchPurchaseFlow(Activity activity) {
        lastPurchaseResult = null;
        
        if (!isConnected || removeAdsProduct == null) {
            lastPurchaseResult = "ERROR:Billing not available";
            Log.e(TAG, "Cannot purchase: not connected or product not loaded");
            return;
        }
        
        List<BillingFlowParams.ProductDetailsParams> productDetailsParamsList = new ArrayList<>();
        productDetailsParamsList.add(
            BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(removeAdsProduct)
                .build()
        );
        
        BillingFlowParams billingFlowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(productDetailsParamsList)
            .build();
        
        BillingResult result = billingClient.launchBillingFlow(activity, billingFlowParams);
        
        if (result.getResponseCode() != BillingClient.BillingResponseCode.OK) {
            lastPurchaseResult = "ERROR:" + result.getDebugMessage();
            Log.e(TAG, "Launch billing flow failed: " + result.getDebugMessage());
        }
    }
    
    @Override
    public void onPurchasesUpdated(BillingResult billingResult, List<Purchase> purchases) {
        if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.OK
                && purchases != null) {
            for (Purchase purchase : purchases) {
                handlePurchase(purchase);
            }
        } else if (billingResult.getResponseCode() == BillingClient.BillingResponseCode.USER_CANCELED) {
            lastPurchaseResult = "ERROR:Purchase cancelled";
            Log.d(TAG, "Purchase cancelled by user");
        } else {
            lastPurchaseResult = "ERROR:" + billingResult.getDebugMessage();
            Log.e(TAG, "Purchase error: " + billingResult.getDebugMessage());
        }
    }
    
    private void handlePurchase(Purchase purchase) {
        if (purchase.getPurchaseState() == Purchase.PurchaseState.PURCHASED) {
            if (purchase.getProducts().contains(REMOVE_ADS_SKU)) {
                isRemoveAdsPurchased = true;
                acknowledgePurchaseIfNeeded(purchase);
                lastPurchaseResult = "SUCCESS:Purchase completed";
                Log.d(TAG, "Remove Ads purchased successfully");
            }
        } else if (purchase.getPurchaseState() == Purchase.PurchaseState.PENDING) {
            lastPurchaseResult = "ERROR:Purchase pending";
            Log.d(TAG, "Purchase pending");
        }
    }
    
    /**
     * Get the last purchase result for polling.
     */
    public static String getLastPurchaseResult() {
        return getInstance().lastPurchaseResult;
    }
    
    /**
     * Check if Remove Ads is purchased.
     */
    public static Boolean isRemoveAdsPurchased() {
        return getInstance().isRemoveAdsPurchased;
    }
    
    /**
     * Restore purchases (queries existing purchases).
     */
    public static void restorePurchases() {
        BillingManager manager = getInstance();
        if (manager.isConnected && manager.billingClient != null) {
            manager.queryExistingPurchases();
        }
    }
    
    /**
     * Clean up resources.
     */
    public static void destroy() {
        BillingManager manager = getInstance();
        if (manager.billingClient != null) {
            manager.billingClient.endConnection();
            manager.billingClient = null;
        }
        manager.isConnected = false;
        Log.d(TAG, "Billing manager destroyed");
    }
}
