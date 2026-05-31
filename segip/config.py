class Config:
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://segip_user:segip_pass@mariadb:3306/segip_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False