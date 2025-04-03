# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run("app_config:create_app", host="0.0.0.0", port=8000, reload=True)
if __name__ == "__main__":
    import os

    os.system(
        # "uvicorn app_config:create_app --host 0.0.0.0 --port 8000 --reload --factory"
        "uvicorn app_config:create_app --host 0.0.0.0 --port 8000 --workers 4 --factory"
    )
