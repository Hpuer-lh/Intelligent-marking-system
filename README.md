# Intelligent-marking-system
PaddleOCR+Ernie Bot+Gradio
graph TD
   仓颉智鉴 --> 精准分析
   仓颉智鉴 --> 批量评阅
   仓颉智鉴 --> 系统操作

    subgraph 精准分析
        direction TB
        精准分析 --> submit_input
        submit_input --> process_file
        process_file --> OCRWrapper["OCRWrapper.ocr.ocr"]
        process_file --> generate_evaluation_base_content
        process_file --> generate_evaluation_prompt
        process_file --> remove_markdown
        process_file --> Chatbot["Chatbot.Siliconflow/ErnieBot"]
        process_file --> pdf["pdf.pdf"]
        精准分析 --> clear_input
        精准分析 --> demo_do
    end

    subgraph 批量评阅
        direction TB
        批量评阅 --> thread_process_files
        thread_process_files --> thread_worker
        thread_worker --> process_file
        thread_process_files --> merge_pdfs["pdf.merge_pdfs"]
        批量评阅 --> clears_input
        批量评阅 --> demos_do
        批量评阅 --> stop_do
    end

    subgraph 系统操作
        direction TB
        系统操作 --> logging_message
        系统操作 --> save_logging
        系统操作 --> delete_datas
        系统操作 --> safe_code
        delete_datas --> hash_string
        delete_datas --> folder_ops["file_folder_operations"]
    end

    style 仓颉智鉴 fill:#FFE4B5,stroke:#FFA07A
    style 精准分析 fill:#E0FFFF,stroke:#20B2AA
    style 批量评阅 fill:#E6E6FA,stroke:#9370DB
    style 系统操作 fill:#F0FFF0,stroke:#32CD32
