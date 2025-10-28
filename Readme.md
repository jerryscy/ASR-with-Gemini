# 使用 Gemini 进行实时转录和翻译

该项目提供了一个使用 WebSocket 和 Web 界面的实时音频转录和翻译服务。它从您的麦克风捕获音频，使用语音活动检测 (VAD) 检测停顿，并将音频发送到 Google Gemini 进行转录和翻译，然后将翻译结果通过文本转语音（TTS）播放。

## 功能

*   **🎤 实时音频流：** 直接从您的麦克风捕获音频。
*   **🗣️ 语音活动检测 (VAD)：** 使用 Silero VAD 智能地分割语音。
*   **🚀 Gemini 集成：** 将音频发送到 Gemini 以进行快速准确的转录和翻译。
*   **🔊 文本转语音（TTS）：** 将翻译的文本转换为语音并播放。
*   **🌐 Web 界面：** 简单直观的界面，便于交互。
*   **📝 累积结果：** 显示完整的转录和翻译历史记录。

## 工作原理

1.  **音频捕获：** 应用程序通过 WebSocket 从用户的麦克风流式传输音频。
2.  **VAD 分割：** Silero VAD 模型检测音频流中的语音和停顿。
3.  **音频聚合：** 将停顿之间的音频块收集到单个段中。
4.  **Gemini 处理：** 将聚合的音频发送到 Gemini 模型进行转录和翻译。
5.  **文本转语音（TTS）：** 将翻译结果发送到 Google Text-to-Speech API 以生成音频。
6.  **播放和显示：** 播放翻译后的音频，并在 Web 界面中实时显示转录和翻译结果。

## 先决条件

*   Python 3.10+
*   Google Cloud SDK

## 安装

1.  **克隆存储库：**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **创建并激活虚拟环境：**
    ```bash
    python3 -m venv myenv
    source myenv/bin/activate
    ```

3.  **安装所需的依赖项：**
    ```bash
    pip install -r requirements.txt
    ```

## 配置和身份验证

1.  **在项目根目录中创建一个 `.env` 文件**，并添加您的 Vertex AI 项目 ID 和位置：
    ```env
    GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
    GOOGLE_CLOUD_LOCATION="your-gcp-location"
    ```

2.  **使用 Google Cloud 进行身份验证：**
    ```bash
    gcloud auth application-default login
    ```

## 用法

1.  **运行应用程序：**
    ```bash
    python3 server.py
    ```

2.  **在浏览器中打开 `index.html` 文件**。

3.  **单击“录制音频（流式）”按钮**并开始讲话。

4.  **讲话后暂停**以触发转录和翻译过程。

5.  **在下方的文本框中查看结果**。

## 故障排除

*   **身份验证错误：** 确保您已使用 `gcloud` 进行身份验证，并在您的 Google Cloud 项目中具有 Vertex AI 或 Gemini API 的必要权限。
*   **麦克风问题：** 检查您的浏览器和系统设置，确保可以访问麦克风。
