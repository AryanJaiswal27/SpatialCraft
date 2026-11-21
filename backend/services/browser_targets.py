from typing import Dict, Any

LLM_TARGET_CONFIGS: Dict[str, Dict[str, Any]] = {
    "chatgpt": {
        "name": "ChatGPT",
        "url": "https://chatgpt.com",
        "file_input_selectors": [
            "input[type='file']",
            "input[data-testid='file-upload-input']",
        ],
        "attach_button_selectors": [
            "button[aria-label*='Attach']",
            "button[data-testid='attach-button']",
            "button[aria-label='Attach files']",
            "button[data-testid='composer-plus-button']",
        ],
        "prompt_input_selectors": [
            "#prompt-textarea",
            "div[contenteditable='true']#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
            "div[contenteditable='true']",
        ],
        "send_button_selectors": [
            "button[data-testid='send-button']",
            "button[aria-label='Send prompt']",
            "button[aria-label='Send message']",
        ],
        "stop_button_selectors": [
            "button[data-testid='stop-button']",
            "button[aria-label='Stop streaming']",
        ],
        "response_selectors": [
            "div[data-message-author-role='assistant']",
            "div[class*='agent-turn']",
            "div.markdown",
        ]
    },
    "claude": {
        "name": "Claude",
        "url": "https://claude.ai/new",
        "file_input_selectors": [
            "input[type='file']",
            "input[accept*='image']",
        ],
        "attach_button_selectors": [
            "button[aria-label*='Upload']",
            "button[aria-label*='Attach']",
            "button[aria-label*='Add content']",
        ],
        "prompt_input_selectors": [
            "div[contenteditable='true'].ProseMirror",
            "div[contenteditable='true']",
            "fieldset div[contenteditable='true']",
        ],
        "send_button_selectors": [
            "button[aria-label*='Send Message']",
            "button[aria-label*='Send message']",
            "button[aria-label='Send']",
            "button[data-testid='send-button']",
        ],
        "stop_button_selectors": [
            "button[aria-label*='Stop']",
        ],
        "response_selectors": [
            ".font-claude-message",
            "div[data-is-streaming='false']",
            "div.standard-markdown",
        ]
    },
    "gemini": {
        "name": "Gemini",
        "url": "https://gemini.google.com/app",
        "file_input_selectors": [
            "input[type='file'][accept*='image']",
            "input[type='file']",
            "input[accept*='image']",
        ],
        "attach_button_selectors": [
            "button[aria-label*='Upload and tools']",
            "button[aria-label*='Upload']",
            "button[aria-label*='Add files']",
            "button.upload-button",
            "button[aria-label*='Attach']",
        ],
        "prompt_input_selectors": [
            "div[contenteditable='true'].ql-editor",
            "rich-textarea div[contenteditable='true']",
            "div[role='textbox']",
            "div[contenteditable='true']",
        ],
        "send_button_selectors": [
            "button[aria-label*='Send message']",
            "button[aria-label*='Send']",
            "button.send-button",
        ],
        "stop_button_selectors": [
            "button[aria-label*='Stop response']",
        ],
        "response_selectors": [
            "message-content",
            "model-response",
            ".markdown",
        ]
    },
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "file_input_selectors": [
            "input[type='file']",
        ],
        "attach_button_selectors": [
            "div[role='button'][aria-label*='Attach']",
            "button[aria-label*='Attach']",
            "div[role='button'][aria-label*='Upload']",
        ],
        "prompt_input_selectors": [
            "textarea#chat-input",
            "textarea[placeholder*='DeepSeek']",
            "textarea",
        ],
        "send_button_selectors": [
            "div[role='button'][aria-label*='Send']",
            "button[aria-label*='Send']",
            "div[aria-label='Send']",
        ],
        "stop_button_selectors": [
            "div[role='button'][aria-label*='Stop']",
        ],
        "response_selectors": [
            ".ds-markdown",
            ".chat-message-assistant",
            "div[class*='markdown']",
        ]
    }
}

