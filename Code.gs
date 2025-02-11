/*
  Code.gs
  =========

  this script converts your google doc into markdown and publishes it to your github pages.
  the conversion now supports standard markdown footnotes so that kramdown outputs a proper 
  <div class="footnotes"> that your sidenotes js can use.
*/

// ======================
// CONFIGURATION
// ======================
const CONFIG = {
  REPO: 'croissanthology/croissanthology.github.io', // Format: 'owner/repo'
  BRANCH: 'main',
  IMAGE_PATH: 'images', // Path in your repository for images
};

// ======================
// SECURE TOKEN HANDLING
// ======================
function getGitHubToken() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  if (!token) throw new Error('GitHub token not configured. Please add it to the script properties.');
  return token;
}

// ======================
// MARKDOWN CONVERSION UTILITIES
// ======================

// updated convertGoogleDocToMarkdown to initialize and append footnotes
function convertGoogleDocToMarkdown(doc) {
  const body = doc.getBody();
  const numChildren = body.getNumChildren();
  let markdown = '';
  
  // initialize state for footnotes: a counter and definitions array
  let state = { footnoteCounter: 1, footnoteDefinitions: [] };
  
  for (let i = 0; i < numChildren; i++) {
    const element = body.getChild(i);
    markdown += processElement(element, state);
  }
  
  // if any footnotes were collected, append them at the end
  if (state.footnoteDefinitions.length > 0) {
    markdown += "\n";
    state.footnoteDefinitions.forEach(def => {
      markdown += def + "\n";
    });
  }
  return markdown;
}

// update processElement to pass along state
function processElement(element, state) {
  let markdown = '';
  const type = element.getType();
  
  switch (type) {
    case DocumentApp.ElementType.PARAGRAPH:
      markdown += processParagraphElement(element, state);
      break;
    case DocumentApp.ElementType.LIST_ITEM:
      markdown += processListItem(element, state);
      break;
    case DocumentApp.ElementType.TABLE:
      markdown += processTable(element, state);
      break;
    default:
      // Handle other element types if needed
      break;
  }
  return markdown;
}

// update processParagraphElement to use state for text processing
function processParagraphElement(paragraph, state) {
  const heading = paragraph.getHeading();
  const attributes = paragraph.getAttributes();
  const indentStart = attributes[DocumentApp.Attribute.INDENT_START] || 0;
  
  // pass state to processTextElements
  let text = processTextElements(paragraph, state);
  const isBlockQuote = indentStart > 0;
  
  switch (heading) {
    case DocumentApp.ParagraphHeading.TITLE:
    case DocumentApp.ParagraphHeading.SUBTITLE:
      // Skip title and subtitle as they are handled separately
      return '';
    case DocumentApp.ParagraphHeading.HEADING1:
      return `\n# ${text}\n`;
    case DocumentApp.ParagraphHeading.HEADING2:
      return `\n## ${text}\n`;
    case DocumentApp.ParagraphHeading.HEADING3:
      return `\n### ${text}\n`;
    case DocumentApp.ParagraphHeading.HEADING4:
      return `\n#### ${text}\n`;
    case DocumentApp.ParagraphHeading.HEADING5:
      return `\n##### ${text}\n`;
    case DocumentApp.ParagraphHeading.HEADING6:
      return `\n###### ${text}\n`;
    case DocumentApp.ParagraphHeading.NORMAL:
    default:
      if (isBlockQuote) {
        // Convert indented paragraphs to block quotes
        return `> ${text}\n`;
      } else {
        return `${text}\n`;
      }
  }
}

// update processTextElements to handle FOOTNOTE elements using state
function processTextElements(element, state) {
  let text = '';
  const numChildren = element.getNumChildren();
  for (let i = 0; i < numChildren; i++) {
    const child = element.getChild(i);
    const type = child.getType();
    if (type === DocumentApp.ElementType.TEXT) {
      // regular text; no change needed
      text += processText(child);
    } else if (type === DocumentApp.ElementType.INLINE_IMAGE) {
      text += processImage(child);
    } else if (type === DocumentApp.ElementType.FOOTNOTE) {
      // process the footnote using the state object
      const footnoteContent = child.getFootnoteContents().getText();
      const marker = state.footnoteCounter++;
      // insert the inline reference marker (e.g. [^1])
      text += `[^${marker}]`;
      // store the definition in the state's accumulator
      state.footnoteDefinitions.push(`[^${marker}]: ${footnoteContent}`);
    }
  }
  return text;
}

// update processListItem to pass state
function processListItem(listItem, state) {
  const glyphType = listItem.getGlyphType();
  let markdown = '';
  const nestingLevel = listItem.getNestingLevel();
  const indent = '  '.repeat(nestingLevel);
  // pass state to processTextElements
  const text = processTextElements(listItem, state);
  
  if (glyphType === DocumentApp.GlyphType.BULLET
      || glyphType === DocumentApp.GlyphType.HOLLOW_BULLET
      || glyphType === DocumentApp.GlyphType.SQUARE_BULLET) {
    markdown += `${indent}- ${text}\n`;
  } else if (glyphType === DocumentApp.GlyphType.NUMBER
      || glyphType === DocumentApp.GlyphType.LATIN_UPPER
      || glyphType === DocumentApp.GlyphType.LATIN_LOWER
      || glyphType === DocumentApp.GlyphType.ROMAN_UPPER
      || glyphType === DocumentApp.GlyphType.ROMAN_LOWER) {
    markdown += `${indent}1. ${text}\n`;
  } else {
    markdown += `${indent}- ${text}\n`;
  }
  return markdown;
}

// update processTable to pass state when processing each cell
function processTable(table, state) {
  let markdown = '\n';
  const numRows = table.getNumRows();
  for (let i = 0; i < numRows; i++) {
    const row = table.getRow(i);
    const numCells = row.getNumCells();
    let rowText = '|';
    for (let j = 0; j < numCells; j++) {
      const cell = row.getCell(j);
      const cellText = processTextElements(cell, state);
      rowText += ` ${cellText} |`;
    }
    markdown += `${rowText}\n`;
    // add a separator after the header row (first row)
    if (i === 0) {
      let separator = '|';
      for (let j = 0; j < numCells; j++) {
        separator += ' --- |';
      }
      markdown += `${separator}\n`;
    }
  }
  markdown += '\n';
  return markdown;
}

// ======================
// OTHER HELPER FUNCTIONS
// ======================

// processText: handles formatting for a Text element
function processText(textElement) {
  let text = '';
  const txt = textElement.getText();
  const attrs = textElement.getTextAttributeIndices();
  
  for (let i = 0; i < attrs.length; i++) {
    const start = attrs[i];
    const end = (i + 1 < attrs.length) ? attrs[i + 1] : txt.length;
    const partText = txt.substring(start, end);
    const partAttr = textElement.getAttributes(start);
    
    let formattedText = partText;
    
    // if URL link exists, process link first
    let isLink = false;
    if (partAttr.LINK_URL) {
      formattedText = `[${formattedText}](${partAttr.LINK_URL})`;
      isLink = true;
    }
    
    // apply formatting
    if (partAttr.BOLD && partAttr.ITALIC) {
      formattedText = `***${formattedText}***`;
    } else if (partAttr.BOLD) {
      formattedText = `**${formattedText}**`;
    } else if (partAttr.ITALIC) {
      formattedText = `*${formattedText}*`;
    }
    
    if (partAttr.STRIKETHROUGH) {
      formattedText = `~~${formattedText}~~`;
    }
    
    // apply underline formatting only if not a link
    if (partAttr.UNDERLINE && !isLink) {
      formattedText = `<u>${formattedText}</u>`;
    }
    
    text += formattedText;
  }
  return text;
}

// processImage: handles inline images
function processImage(inlineImage) {
  const blob = inlineImage.getBlob();
  const contentType = blob.getContentType();
  let extension = '';
  
  switch (contentType) {
    case 'image/jpeg':
      extension = '.jpg';
      break;
    case 'image/png':
      extension = '.png';
      break;
    case 'image/gif':
      extension = '.gif';
      break;
    default:
      // unsupported image type
      return '';
  }
  
  const imageName = `image_${new Date().getTime()}${extension}`;
  const imageUrl = uploadImageToGitHub(imageName, blob);
  
  return `![Image](${imageUrl})`;
}

// ======================
// GITHUB API HANDLER WITH ERROR HANDLING
// ======================
function githubApi(urlPath, method = 'GET', data = null) {
  const url = `https://api.github.com/repos/${CONFIG.REPO}/${urlPath}`;
  const options = {
    method: method,
    headers: {
      'Authorization': `token ${getGitHubToken()}`,
      'Accept': 'application/vnd.github.v3+json'
    },
    muteHttpExceptions: true
  };
  if (data) {
    options.contentType = 'application/json';
    options.payload = JSON.stringify(data);
  }
  const response = UrlFetchApp.fetch(url, options);
  const statusCode = response.getResponseCode();
  
  if (statusCode >= 200 && statusCode < 300) {
    return JSON.parse(response.getContentText());
  } else {
    const error = JSON.parse(response.getContentText());
    console.error(`GitHub API Error (${statusCode}): ${error.message}`);
    throw new Error(`GitHub API Error: ${error.message}`);
  }
}

function uploadImageToGitHub(imageName, blob) {
  const content = Utilities.base64Encode(blob.getBytes());
  const path = `contents/${CONFIG.IMAGE_PATH}/${encodeURIComponent(imageName)}`;
  const data = {
    message: `Add image ${imageName}`,
    content: content,
    branch: CONFIG.BRANCH
  };
  try {
    const result = githubApi(path, 'PUT', data);
    // return the raw url to access the image
    return `https://raw.githubusercontent.com/${CONFIG.REPO}/${CONFIG.BRANCH}/${CONFIG.IMAGE_PATH}/${encodeURIComponent(imageName)}`;
  } catch (e) {
    console.error(`Failed to upload image: ${e.message}`);
    throw e;
  }
}

function commitPost(fileName, content) {
  const encodedContent = Utilities.base64Encode(Utf8.encode(content));
  const endpoint = `contents/_posts/${encodeURIComponent(fileName)}`;
  
  try {
    // check if file exists
    const existing = githubApi(endpoint);
    const data = {
      message: `Update post: ${fileName}`,
      content: encodedContent,
      sha: existing.sha,
      branch: CONFIG.BRANCH
    };
    return githubApi(endpoint, 'PUT', data);
  } catch (e) {
    if (e.message.includes('Not Found')) {
      // file doesn't exist, create new
      const data = {
        message: `Create new post: ${fileName}`,
        content: encodedContent,
        branch: CONFIG.BRANCH
      };
      return githubApi(endpoint, 'PUT', data);
    } else {
      console.error(`Failed to commit post: ${e.message}`);
      throw e;
    }
  }
}

function updateIndex(newTitle, newUrl) {
  try {
    const indexPath = 'contents/index.html';
    const currentIndex = githubApi(indexPath);
    const content = Utilities.newBlob(Utilities.base64Decode(currentIndex.content)).getDataAsString('UTF-8');
    
    // extract existing list items
    const listMatch = content.match(/(<ul[^>]*>)([\s\S]*?)(<\/ul>)/);
    if (!listMatch) throw new Error('Could not find the post list in index.html');
    
    let [fullMatch, startTag, listItems, endTag] = listMatch;
    const existingItems = listItems.match(/<li>[\s\S]*?<\/li>/g) || [];
    
    // prevent duplicates
    if (existingItems.some(item => item.includes(newUrl))) {
      console.log(`Already listed in index: ${newUrl}`);
      return;
    }
    
    // create new item and maintain 5-item limit
    const newItem = `<li><a href="${newUrl}">${newTitle}</a></li>`;
    const updatedItems = [newItem, ...existingItems].slice(0, 5);
    
    // rebuild content
    const updatedList = `${startTag}\n${updatedItems.join('\n')}\n${endTag}`;
    const updatedContent = content.replace(fullMatch, updatedList);
    
    // commit changes
    const data = {
      message: `Update index with: ${newTitle}`,
      content: Utilities.base64Encode(Utf8.encode(updatedContent)),
      sha: currentIndex.sha,
      branch: CONFIG.BRANCH
    };
    githubApi(indexPath, 'PUT', data);
  } catch (e) {
    console.error(`Index update failed: ${e.message}`);
    throw e;
  }
}

// ======================
// VALIDATED PUBLISHING WORKFLOW
// ======================
function validateDocument(doc) {
  const body = doc.getBody();
  const paragraphs = body.getParagraphs();
  if (!paragraphs.length) throw new Error('Document is empty');
  
  const titlePara = paragraphs.find(p => p.getHeading() === DocumentApp.ParagraphHeading.TITLE);
  if (!titlePara) throw new Error('Document missing title paragraph');
  
  const dateParagraph = paragraphs.find(p => p.getHeading() === DocumentApp.ParagraphHeading.SUBTITLE);
  if (!dateParagraph) throw new Error('Document missing date in subtitle paragraph');
  
  const dateMatch = dateParagraph.getText().match(/\d{4}-\d{2}-\d{2}/);
  if (!dateMatch) throw new Error('Invalid date format in subtitle (use YYYY-MM-DD)');
}

function publishToBlog() {
  try {
    const doc = DocumentApp.getActiveDocument();
    validateDocument(doc);
    
    const docTitle = doc.getName(); // name of the google doc
    
    const body = doc.getBody();
    const paragraphs = body.getParagraphs();
    
    const titlePara = paragraphs.find(p => p.getHeading() === DocumentApp.ParagraphHeading.TITLE);
    const datePara = paragraphs.find(p => p.getHeading() === DocumentApp.ParagraphHeading.SUBTITLE);
    
    const title = titlePara.getText(); // title from the document's content
    const dateMatch = datePara.getText().match(/\d{4}-\d{2}-\d{2}/);
    const date = dateMatch[0];
    
    // use docTitle to generate the permalink and slug
    const urlTitle = docTitle.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
    const fileName = `${date}-${urlTitle}.md`;
    
    // generate markdown content
    let markdown = `---
layout: post
title: "${title}" 
date: ${date}
permalink: /${urlTitle} 
---

`;
    // generate markdown from document
    const contentMarkdown = convertGoogleDocToMarkdown(doc);
    markdown += contentMarkdown;
    
    // commit changes
    const result = commitPost(fileName, markdown);
    
    // update index with the post's title and permalink
    updateIndex(title, `/${urlTitle}`);
    
    DocumentApp.getUi().alert(`Success! Your post has been published.`);
    
  } catch (e) {
    DocumentApp.getUi().alert(`Error: ${e.message}`);
    console.error(e);
  }
}

// ======================
// MENU SETUP
// ======================
function onOpen() {
  DocumentApp.getUi()
    .createMenu('Blog Tools')
    .addItem('Publish Post', 'publishToBlog')
    .addToUi();
}

// ======================
// UTILITY FOR UTF-8 ENCODING
// ======================
const Utf8 = {
  encode: function (string) {
    return Utilities.newBlob(string).getBytes();
  }
}; 