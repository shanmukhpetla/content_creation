**Guide: Installing and Running the FastAPI Video Processing Project in Visual Studio Code**

## Prerequisites
Before setting up and running the project, ensure you have the following installed on your system:
- **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
- **pip** (Python package manager)
- **Visual Studio Code**: Download from [code.visualstudio.com](https://code.visualstudio.com/)
- **Git** (optional but recommended)

---
## Step 1: Clone the Repository (Optional)
If you have the project in a Git repository, clone it using:
```sh
git clone <repository_url>
cd <project_folder>
```
Otherwise, create a new folder and place your project files there.

---
## Step 2: Open the Project in Visual Studio Code
1. Open **Visual Studio Code**.
2. Click **File** > **Open Folder...**
3. Select the project folder.

---
## Step 3: Create and Activate a Virtual Environment
It's recommended to use a virtual environment to manage dependencies.

### On Windows:
```sh
python -m venv venv
venv\Scripts\activate
```

### On macOS/Linux:
```sh
python3 -m venv venv
source venv/bin/activate
```

---
## Step 4: Install Dependencies
Run the following command in the terminal to install required packages:
```sh
pip install -r requirements.txt
```

---
## Step 5: Create a `.env` File
The `.env` file is required to store the **OpenAI API Key**. Create a new file named `.env` in the project root directory and add:
```
OPENAI_API_KEY=your_api_key_here
```
Replace `your_api_key_here` with your actual OpenAI API key.

---
## Step 6: Run the FastAPI Server
Start the FastAPI server with:
```sh
uvicorn main:app --reload
```

If everything is set up correctly, you should see an output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---
## Step 7: Test the API in the Browser
1. Open your browser and go to:
   ```
   http://127.0.0.1:8000/docs
   ```
2. This will open the **Swagger UI**, where you can test different API endpoints.

---
## Step 8: Use the CLI (Optional)
To run the CLI script, use:
```sh
python cli.py <video_file_path> --reel_start 10 --reel_end 30 --thumbnail_time 15
```
Replace `<video_file_path>` with the path to your video file.

---
## Step 9: Stopping the Server
To stop the FastAPI server, press **CTRL + C** in the terminal.

---
## Troubleshooting
- If dependencies fail to install, ensure you are using the correct Python version.
- If `.env` variables are not loading, restart your terminal and try again.
- If FastAPI does not start, ensure `uvicorn` is installed and the `main.py` file exists.

---
### Now your FastAPI video processing project is successfully set up and running!

