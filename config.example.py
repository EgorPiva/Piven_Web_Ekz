"""Example configuration for exam deployment.

Copy this file to ``instance/config.py`` and replace the placeholders with
your own values before launching the project on the university host.
"""

SECRET_KEY = "change-me-on-the-host"
SQLALCHEMY_DATABASE_URI = (
    "mysql+pymysql://std_NNNN_exam:<password>@std-mysql/std_NNNN_exam"
    "?charset=utf8mb4"
)

# Optional metadata shown by the application.
STUDENT_GROUP = "241-371"
STUDENT_NAME = "Пивень Егор"
