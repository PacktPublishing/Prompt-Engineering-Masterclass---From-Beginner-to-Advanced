# Prompt Engineering Masterclass: From Beginner to Advanced

This repository contains all the code and materials for my course, **Prompt Engineering Masterclass: From Beginner to Advanced**.

**Note:** The final project, the `ai-toolbox` CLI tool, is built progressively in its own repository. All code for the project is available for download as well.

## Welcome!

I'm thrilled to have you here! This repository contains all the notebooks and supplementary materials for the course. My goal is to provide you with practical, real-world examples that will help you master Prompt Engineering and build your own powerful, AI-driven developer tools.

## 🚀 Getting Started

To run the code examples locally, you'll need to set up your environment correctly. It is highly recommended to use a virtual environment to keep project dependencies isolated.

**IMPORTANT**: Make sure to have **Python 3.13.3** installed to follow along without running into any issues 😊 This version ensures full compatibility with all the libraries and features used throughout the course.

1.  **Clone the Repository**
2.  **Create and Activate a Virtual Environment**
    Create a new virtual environment (the conventional name is `.venv`):

    ```bash
    python3 -m venv .venv
    ```

    Activate it for your current shell session:

    ```bash
    # On macOS and Linux
    source .venv/bin/activate

    # On Windows
    .venv\Scripts\activate
    ```

    Your shell prompt should now be prefixed with `(.venv)`, indicating the environment is active.

3.  **Set Up API Keys**
    This course requires API keys from LLM providers. Copy the example environment file:

    ```bash
    cp .env.example .env
    ```

    Now, open the `.env` file and add your secret API keys. You will need at least one key (e.g., from OpenAI) to follow along.

    ```env
    OPENAI_API_KEY="sk-..."
    ANTHROPIC_API_KEY="sk-ant-..."
    ```

4.  **Install Dependencies**
    The required packages for this course are listed in `requirements.txt`. Install them using pip:

    ```bash
    pip install -r requirements.txt
    ```

5.  **Launch JupyterLab**
    Many of the initial lectures use Jupyter Notebooks (`.ipynb` files) for interactive demonstrations. You can launch the JupyterLab interface by running:
    ```bash
    jupyter lab
    ```
    This will open a new tab in your web browser, allowing you to navigate the project folders and open any `.ipynb` notebook files.

## 🧑‍💻 Following Along with the Course

This repository has two primary branches to support your learning (if you downloaded the files, you will have two downloads, one per branch):

- **`main` branch**: This branch contains the final, completed code for every lecture. Use it as a reference if you get stuck or want to see the finished solution.
- **`start` branch**: This branch is designed for you to follow along with the hands-on lectures. It contains the initial state for each lesson, including notebooks and project files, but with the code blocks often left for you to complete.

To switch to the `start` branch and code along with me, run:

```bash
git checkout start
```

## 📚 Course Structure

The repository is organized into modules, each corresponding to a section in the course. Here is an overview of what you will learn:

- **Tools and Local Setup**: Get your machine ready by setting up the correct Python version and generating the necessary API keys from providers like OpenAI and Anthropic.

- **OpenAI API Crash Course**: Master the fundamentals of interacting with LLMs. This module covers authentication, your first API calls, using LiteLLM for provider-agnostic code, controlling output with parameters, and implementing streaming.

- **AI Toolbox Setup**: Build the foundation of our course project. You will use an AI agent to scaffold a complete Python project, implement a CLI with Click, and create your first simple AI-powered command.

- **Foundations of Large Language Models**: Dive deep into the core mechanics of LLMs. This module covers the critical concepts of tokenization, the context window, API cost calculation, and the strategic use of system, user, and assistant prompt roles.

- **Core Prompting Patterns**: Learn the essential toolkit of a prompt engineer. This section covers foundational patterns like Instruction-Context-Constraint, the power of Delimiters, the Persona Pattern, Few-Shot Prompting, and Chain-of-Thought.

- **AI Toolbox: Smart Commits**: Implement the first major feature of our AI Toolbox. You will build an AI-powered `commit` command that reads staged git changes and generates high-quality, conventional commit messages automatically.

- **Advanced Prompting Techniques**: Move on to sophisticated, multi-step strategies. This module covers advanced patterns like Flip the Script, Decomposition, Self-Critique, Self-Consistency, and enabling your AI to use external tools with Function Calling.

- **AI Toolbox: Smart Reviews**: Build the most advanced feature of our project: a `review` command that uses a multi-persona pipeline to perform a detailed code review, integrates external linters, and uses a self-critique step to deliver a polished final report.

- **AI Toolbox: JSON and Markdown Output**: Finalize the project by refactoring for production readiness. You will migrate the entire review pipeline from handling plain text to using structured, machine-readable data objects, and add CLI options to output the final report as either JSON or Markdown.

I'm looking forward to seeing you in the course.
