# config_prod.py
import os

# Токен бота (тот же)
BOT_TOKEN = "8601561728:AAFoF_epJFYk9XyZpQtSEg-RjnDahU4i2lk"

# ID администратора
ADMIN_ID = 1332239711  # замени на свой

# Контакт техподдержки
SUPPORT_USERNAME = "@huhmek26"

# Пароль для админки
ADMIN_PASSWORD = "tabakmen1823*4"

# Настройки базы данных - для Railway используем PostgreSQL
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tabakmen.db')