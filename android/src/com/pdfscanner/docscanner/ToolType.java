package com.pdfscanner.docscanner;

/**
 * Enum for annotation/editing tool types.
 */
public enum ToolType {
    NONE,           // No tool selected (pan/zoom mode)
    HIGHLIGHT,      // Yellow highlight annotation
    UNDERLINE,      // Underline annotation
    STRIKEOUT,      // Strikethrough annotation
    PEN,            // Freehand ink drawing
    ERASER,         // Erase ink strokes
    REDACT_BLACK,   // Black redaction rectangle
    REDACT_WHITE,   // White/whiteout rectangle
    TEXT,           // Add text box
    SIGNATURE       // Place signature
}
