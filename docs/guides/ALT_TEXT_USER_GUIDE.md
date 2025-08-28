# Alt Text User Guide

## Overview

FootFix's AI-powered alt text generation feature helps editorial teams create professional, accessibility-compliant descriptions for images using Anthropic's Claude Vision API. This guide covers setup, usage, best practices, and troubleshooting.

## Table of Contents

1. [Getting Started](#getting-started)
2. [API Setup](#api-setup)
3. [Generating Alt Text](#generating-alt-text)
4. [Reviewing and Editing](#reviewing-and-editing)
5. [Exporting Alt Text](#exporting-alt-text)
6. [Best Practices](#best-practices)
7. [Cost Management](#cost-management)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### What is Alt Text?

Alt text (alternative text) provides textual descriptions of images for:
- Screen reader users
- Search engine optimization
- Situations where images fail to load
- Content management systems

### Requirements

- FootFix v1.1 or later
- Anthropic API key (Claude Vision access)
- Internet connection for API calls
- Supported image formats: JPEG, PNG, WebP, TIFF

## API Setup

### Obtaining an Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key for FootFix
5. Copy the key (starts with `sk-ant-api...`)

### Configuring FootFix

1. Open FootFix Preferences (⌘,)
2. Navigate to the "Alt Text" tab
3. Enter your API key in the secure field
4. Click "Validate Key" to test connection
5. Configure cost tracking preferences (optional)

## Generating Alt Text

### Single Image Generation

1. Process your images normally in FootFix
2. Switch to the "Alt Text" tab
3. Click "Generate Alt Text" for individual images
4. Wait for AI processing (typically 2-5 seconds per image)

### Batch Generation

1. Select multiple processed images
2. Click "Generate Alt Text for All"
3. Monitor progress in the status bar
4. Review results as they complete

### Generation Settings

- **Context**: Optionally provide context (e.g., "fashion editorial", "product shot")
- **Rate Limiting**: Automatic handling of API rate limits
- **Retry Logic**: Failed requests automatically retry up to 3 times

## Reviewing and Editing

### Alt Text Review Interface

The review interface displays:
- Image thumbnail
- Generated alt text
- Character count indicator
- Status (completed, error, pending)
- Edit capabilities

### Editing Alt Text

1. Click in the text field to edit
2. Character count updates in real-time:
   - Green: Under 100 characters (optimal)
   - Orange: 100-125 characters (warning)
   - Red: Over 125 characters (too long)
3. Changes save automatically

### Bulk Actions

- **Select All**: Check all items for bulk operations
- **Approve All**: Accept all generated descriptions
- **Regenerate Selected**: Re-generate specific items

### Quality Guidelines

#### Good Alt Text Examples:
- "Woman in navy dress walking through autumn leaves"
- "Silver watch with black dial on white background"
- "Coffee shop interior with wooden tables and natural lighting"

#### Avoid:
- "Image of..." or "Picture of..." (redundant)
- File names or extensions
- Overly generic descriptions
- Excessive detail beyond 125 characters

## Exporting Alt Text

### Export Formats

#### CSV Export
Best for:
- Spreadsheet review
- Bulk editing
- Data analysis

Includes:
- Filename
- Alt text
- Image dimensions
- Processing status
- API cost per image

#### JSON Export
Best for:
- Developer integration
- Detailed metadata
- Automated workflows

Includes:
- Complete metadata
- Usage statistics
- Processing timestamps
- Hierarchical data structure

#### WordPress Export
Optimized for WordPress Media Library import:
- Formatted CSV with proper column names
- Title generation from filenames
- Compatible with WP All Import plugin

### Export Workflow

1. Click the Export button dropdown
2. Select format (CSV, JSON, or WordPress)
3. Choose export scope:
   - All Items
   - Selected Only
   - Completed Only
4. Select save location
5. Review exported file

### CMS Integration

#### WordPress Import
1. Export as WordPress CSV
2. Use WP All Import or similar plugin
3. Map fields:
   - filename → Image filename
   - alt_text → Alt text field
   - title → Image title

#### Other CMS Platforms
Use JSON export for custom integration with:
- Drupal
- Contentful
- Shopify
- Custom CMS solutions

## Best Practices

### Editorial Guidelines

1. **Be Descriptive Yet Concise**
   - Aim for 50-125 characters
   - Focus on key visual elements
   - Include relevant context

2. **Consider Your Audience**
   - Fashion: Include style, color, fit
   - Products: Highlight features, materials
   - Lifestyle: Describe mood, setting

3. **Maintain Consistency**
   - Use consistent terminology
   - Follow brand voice guidelines
   - Apply uniform style across collections

### Technical Best Practices

1. **Image Optimization**
   - Process images before alt text generation
   - Ensure good image quality for better AI analysis
   - Batch similar images together

2. **Workflow Efficiency**
   - Generate alt text after image processing
   - Review in batches by category
   - Export regularly to avoid data loss

3. **Quality Assurance**
   - Always review AI-generated text
   - Edit for brand voice and accuracy
   - Check character counts

## Cost Management

### Understanding Costs

- Current rate: ~$0.006 per image
- Billed through Anthropic account
- No FootFix markup or fees

### Cost Tracking

FootFix tracks:
- Total API requests
- Cumulative costs
- Monthly usage
- Per-batch costs

View statistics:
1. Open Preferences
2. Navigate to Alt Text tab
3. Click "View Usage Statistics"

### Cost Optimization

1. **Batch Processing**
   - Process similar images together
   - Avoid regenerating unchanged images

2. **Selective Generation**
   - Only generate for images needing alt text
   - Skip decorative or redundant images

3. **Monthly Budgeting**
   - Estimate: 1,000 images ≈ $6.00
   - Set monthly limits in Anthropic console
   - Monitor usage regularly

### Budget Estimation

| Images/Month | Estimated Cost |
|--------------|----------------|
| 100          | $0.60          |
| 500          | $3.00          |
| 1,000        | $6.00          |
| 5,000        | $30.00         |
| 10,000       | $60.00         |

## Troubleshooting

### Common Issues

#### "API Key Invalid"
- Verify key is correctly entered
- Check Anthropic account status
- Ensure API access is enabled

#### "Rate Limited"
- FootFix automatically handles rate limits
- Wait for retry or try again later
- Consider upgrading Anthropic plan

#### "Network Error"
- Check internet connection
- Verify firewall settings
- Try again after network stabilizes

#### "Image Encoding Failed"
- Ensure image file is not corrupted
- Check supported formats
- Try re-saving the image

### Error Recovery

1. **Individual Failures**
   - Use "Regenerate" button
   - Check error message for details
   - Edit manually if needed

2. **Batch Failures**
   - Select failed items
   - Click "Regenerate Selected"
   - Export successful items first

3. **Persistent Issues**
   - Check Anthropic API status
   - Verify account limits
   - Contact support with error details

### Performance Tips

1. **Optimal Batch Sizes**
   - 20-30 images per batch
   - Larger batches may hit rate limits

2. **Image Preparation**
   - Resize very large images first
   - Ensure good lighting and clarity
   - Remove unnecessary elements

3. **Network Optimization**
   - Use stable internet connection
   - Avoid VPN if experiencing issues
   - Process during off-peak hours

## Advanced Features

### Custom Context

Provide specific context for better results:
```
Context examples:
- "fashion editorial spring collection"
- "product photography for e-commerce"
- "lifestyle blog hero images"
- "social media campaign visuals"
```

### Keyboard Shortcuts

- `⌘G`: Generate alt text for selected
- `⌘R`: Regenerate current item
- `⌘E`: Export alt text
- `Tab`: Navigate between items

### Integration with Existing Workflow

1. **Presets**: Save alt text with image presets
2. **Batch Templates**: Apply naming conventions
3. **Export Automation**: Schedule regular exports

## Support Resources

### Getting Help

1. **In-App Help**: Access guide from Help menu
2. **Error Messages**: Include detailed diagnostics
3. **Usage Statistics**: Track performance metrics

### Updates and Improvements

FootFix alt text features are regularly updated:
- Improved AI models
- New export formats
- Enhanced editing tools
- Performance optimizations

Stay updated by:
- Checking for FootFix updates
- Reading release notes
- Following best practices

## Conclusion

FootFix's alt text generation streamlines the creation of professional, accessible image descriptions. By following this guide and best practices, editorial teams can efficiently produce high-quality alt text that enhances content accessibility and SEO while maintaining brand consistency.

For additional support or feature requests, please visit the FootFix support portal or contact our team directly.