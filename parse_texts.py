import xml.etree.ElementTree as ET
from datetime import datetime
import html

def convert_backup_to_html(xml_file, output_html_file, filter_number=None):
    print(f"Parsing {xml_file}...")
    
    html_content = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f9fafb; margin: 20px; }",
        ".chat-container { max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; }",
        ".msg { margin: 8px 0; padding: 12px 16px; border-radius: 18px; max-width: 75%; line-height: 1.4; word-wrap: break-word; }",
        ".received { background-color: #e5e5ea; color: #000; align-self: flex-start; border-bottom-left-radius: 4px; }",
        ".sent { background-color: #007aff; color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }",
        ".meta { font-size: 11px; margin-bottom: 4px; opacity: 0.7; }",
        ".attachment { font-style: italic; opacity: 0.9; }",
        "img { max-width: 100%; border-radius: 8px; margin-top: 8px; display: block; }",
        "</style></head><body><div class='chat-container'>"
    ]
    
    with open(output_html_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_content))
    
    msg_count = 0
    context = ET.iterparse(xml_file, events=('end',))
    
    with open(output_html_file, 'a', encoding='utf-8') as f:
        for event, elem in context:
            if elem.tag in ['sms', 'mms']:
                address = str(elem.get('address', ''))
                
                if filter_number and filter_number not in address:
                    elem.clear()
                    continue
                
                date_ms = int(elem.get('date', 0))
                dt = datetime.fromtimestamp(date_ms / 1000.0).strftime('%b %d, %Y %I:%M %p')
                
                # Handle standard SMS
                if elem.tag == 'sms':
                    msg_type = elem.get('type') # '1' is received, '2' is sent
                    body = elem.get('body', '')
                    safe_body = html.escape(body).replace('\n', '<br>')
                
                # Handle MMS (long texts, group chats, images)
                else: 
                    msg_type = elem.get('msg_box') # '1' is received, '2' is sent
                    text_parts = []
                    
                    for part in elem.findall('.//part'):
                        ct = part.get('ct', '')
                        t = part.get('text', '')
                        data = part.get('data', '')
                        
                        # Bypass SMIL layout metadata
                        if ct == 'application/smil':
                            continue
                            
                        # If it's an image and contains base64 data, render the image tag
                        if 'image' in ct and data and data != 'null':
                            img_html = f"<img src='data:{ct};base64,{data}'>"
                            text_parts.append(img_html)
                        
                        # If it's standard text, escape it safely
                        elif t and t != 'null':
                            safe_text = html.escape(t).replace('\n', '<br>')
                            text_parts.append(safe_text)
                            
                        # Fallback for missing image data
                        elif 'image' in ct:
                            img_name = part.get('name', 'image')
                            text_parts.append(f"<span class='attachment'>[Attachment missing data: {img_name}]</span>")
                    
                    # Join the parts with line breaks
                    safe_body = "<br>".join(text_parts)

                if msg_type == "2":
                    css_class = "sent"
                    sender = "Me"
                else:
                    css_class = "received"
                    sender = address
                
                bubble = (
                    f"<div class='msg {css_class}'>"
                    f"<div class='meta'>{sender} • {dt}</div>"
                    f"<div>{safe_body}</div>"
                    f"</div>\n"
                )
                f.write(bubble)
                msg_count += 1
                
                elem.clear()

        f.write("</div></body></html>")
        
    print(f"Done! Wrote {msg_count} messages to {output_html_file}")

# Execute the parser
convert_backup_to_html(
    xml_file='sms-20260919074728.xml', 
    output_html_file='readable_texts.html',
    filter_number=None
)
