работает камера и выбор из галереи, а также выбор линии, но логики пока нет

структура проекта:
.
├── AndroidManifest.tmpl.xml
│
├── Assets
│   │
│   └── fonts
│
├── app.kv
│
├── buildozer.spec
│
├── core
│   │
│   ├── __init__.py
│   │
│   ├── image_loader.py
│   │
│   ├── line_path.py
│   │
│   ├── profile_builder.py
│   │
│   ├── relay_controller.py
│   │
│   └── slope_solver.py
│
├── main.py
│
├── provider_paths.xml
│
├── requirements.txt
│
├── screens
│   │
│   ├── __init__.py
│   │
│   ├── camera_screen.py
│   │
│   ├── line_select_screen.py
│   │
│   ├── profile_screen.py
│   │
│   ├── result_screen.py
│   │
│   └── start_screen.py
│
└── widgets
    ├── __init__.py
