class Config:
    SECRET_KEY = 'safeswipe-secret-key'

    #  MySQL DB configuration
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/Envy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

     #  Email settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'somamca2025@gmail.com'
    MAIL_PASSWORD = 'xtmp cgfg ogel rhwh'
    MAIL_DEFAULT_SENDER = 'somamca2025@gmail.com'
    