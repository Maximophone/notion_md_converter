# Notion Page Duplicator

This project contains two Python scripts to duplicate a Notion page, including all of its content and nested blocks.

## Setup

1.  **Clone the repository (or download the files).**

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/Scripts/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a Notion Integration:**
    *   Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations).
    *   Click "+ New integration".
    *   Give it a name, associate it with a workspace, and submit.
    *   On the next page, under "Capabilities", make sure "Read content", "Update content", and "Insert content" are all enabled.
    *   Copy the "Internal Integration Token".

5.  **Set up environment variables:**
    *   Create a `.env` file in the project root by copying the `.env.example` file.
    *   Add your Notion token to the `.env` file:
        ```
        NOTION_TOKEN="your_internal_integration_token"
        ```

6.  **Configure Page URLs:**
    *   Create a `config.json` file by copying the `config.json.example` file.
    *   Inside `config.json`, replace the placeholder URLs with the full URLs of your source and parent pages.
        ```json
        {
            "source_page_url": "https://www.notion.so/your-workspace/Your-Source-Page-Title-24a865260e43813180f0e007bc6e0ff3",
            "parent_page_url": "https://www.notion.so/your-workspace/Your-Parent-Page-Title-some-other-id"
        }
        ```

7.  **Share the relevant pages with your integration:**
    *   You must share both the **source page** and the **parent page** with your integration.
    *   For each page, click the "..." menu -> "Add connections" -> and select your integration.

## Usage

The process is a two-step workflow.

### Step 1: Fetch the source page content

Run the `fetch_page.py` script. It will read the `source_page_url` from your `config.json`.

```bash
python fetch_page.py
```

This will create a JSON file in the project directory named after the page ID (e.g., `24a865260e43813180f0e007bc6e0ff3.json`).

### Step 2: Create the new page

Run the `convert_and_create_page.py` script. It will read the necessary info from your `config.json` to find the correct input file and determine where to create the new page.

```bash
python convert_and_create_page.py
```

The script will create a new page with the same content as the source page and will output its URL.