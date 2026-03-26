# Sprint v1 — PRD: Paper2Notebook

## Overview
Build a web application that accepts a research paper PDF, extracts its content, and uses OpenAI's GPT-4o to generate a Google Colab-compatible Jupyter notebook. The notebook implements the paper's algorithms and methodology as a tutorial with code, explanations, and visualizations. Users provide their own OpenAI API key via the frontend.

## Goals
- User can upload a research paper PDF and enter their OpenAI API key
- Backend extracts text and structure from the PDF
- GPT-4o generates a tutorial notebook with code cells, markdown explanations, and visualization cells
- User can preview the generated notebook in the browser
- User can download the `.ipynb` file ready for Google Colab

## User Stories
- As a researcher, I want to upload a paper PDF, so that I get a runnable tutorial implementing its key algorithms
- As a student, I want explanatory markdown cells alongside code, so that I can learn the methodology step-by-step
- As a user, I want to preview the notebook before downloading, so that I can verify the output quality
- As a user, I want to use my own OpenAI API key, so that I control my usage and costs

## Technical Architecture

### Tech Stack
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python)
- **PDF Parsing**: PyMuPDF (`fitz`)
- **LLM**: OpenAI GPT-4o via `openai` Python SDK
- **Notebook Generation**: `nbformat` Python library
- **Notebook Preview**: `@nteract/presentational-components` or custom renderer

### Component Diagram
```
┌─────────────────────────────────────┐
│           Next.js Frontend          │
│  ┌───────────┐  ┌────────────────┐  │
│  │ Upload +  │  │   Notebook     │  │
│  │ API Key   │  │   Preview +    │  │
│  │ Form      │  │   Download     │  │
│  └─────┬─────┘  └───────▲────────┘  │
│        │                │            │
└────────┼────────────────┼────────────┘
         │  POST /generate│  JSON (.ipynb)
         ▼                │
┌────────────────────────────────────┐
│          FastAPI Backend           │
│  ┌──────────┐  ┌───────────────┐  │
│  │ PDF      │  │ Notebook      │  │
│  │ Parser   │──│ Generator     │  │
│  │ (PyMuPDF)│  │ (nbformat)    │  │
│  └──────────┘  └───────┬───────┘  │
│                        │           │
│                ┌───────▼───────┐   │
│                │ OpenAI GPT-4o │   │
│                │ (user's key)  │   │
│                └───────────────┘   │
└────────────────────────────────────┘
```

### Data Flow
1. User enters OpenAI API key and uploads PDF on frontend
2. Frontend sends PDF + API key to `POST /api/generate`
3. Backend extracts text from PDF using PyMuPDF
4. Backend sends extracted text to GPT-4o with a structured prompt requesting tutorial notebook content
5. Backend parses GPT-4o response and builds `.ipynb` using `nbformat`
6. Backend returns the `.ipynb` JSON to frontend
7. Frontend renders a preview and offers a download button

## Out of Scope (v2+)
- User accounts / authentication
- Saving/history of generated notebooks
- Multiple LLM provider support (Anthropic, Gemini, etc.)
- Streaming generation progress
- Custom notebook templates or styles
- Batch processing of multiple PDFs
- Editing the notebook in-browser

## Dependencies
- None (greenfield project)
- User must have an OpenAI API key with GPT-4o access
