# 🚧 Project Under Development

This project is currently in active development and is not ready for production use. The source code is organized under the `pytracker` directory.

🔧 **About the Project**

The tool aims to monitor user activity such as:
- Screen time tracking
- App-wise usage tracking
- Dynamic break time detection
- Real-time logging and analytics
- Keeps the user away from distractions by blocking selective apps
- Stores the history into a dynamic-local database powered by `sqlite3`

⏳ Features are being incrementally added and improved. Please expect rapid changes and potential instability during this phase.

---

📁 **Source Code Directory**  
All core functionality are scattered across folder. Check out with patience.

---

## 🛠️ Requirements

- OS : Microsoft Windows 10 and above.
- Python 3.8+
- Packages:
  ```bash
  pip install -r requirements.txt

📌 **Note:**  
Feel free to explore the code, but refrain from deploying it in its current form until a stable release is announced.

## 🚀 Performance Optimizations

The application has been optimized for better performance on low-end devices:

### **Automatic Performance Detection**
- **Memory-based**: Automatically detects devices with < 4GB RAM
- **CPU-based**: Optimizes for devices with < 4 CPU cores
- **Fallback**: Graceful degradation if system detection fails

### **Performance Features**
- **Reduced Update Frequency**: 1-2 second intervals instead of 500ms
- **Image Caching**: Icons and images are cached to reduce I/O
- **Widget Recycling**: Efficient widget management and cleanup
- **Simplified Layouts**: Reduced nested frames and complex layouts
- **Font Size Optimization**: Smaller fonts on low-end devices
- **Lazy Loading**: Widgets created only when needed

### **Low-End Device Optimizations**
- Update intervals increased to 2 seconds
- Font sizes reduced by 20%
- Simplified UI components
- Reduced sample data in history views
- Optimized memory usage

Stay tuned for updates! 🚀
