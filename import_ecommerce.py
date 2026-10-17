import os
import pandas as pd
from sqlalchemy import create_engine

# 1. 连接数据库
db_password = os.getenv("MYSQL_PASSWORD")
engine = create_engine(f'mysql+pymysql://root:{db_password}@localhost:3306/sql_practice')

# 2. 列出所有要导入的 CSV 文件（必须和你下载的文件名一模一样，注意大小写）
files = {
    'customers': 'olist_customers_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'payments': 'olist_order_payments_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'reviews': 'olist_order_reviews_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'geolocation': 'olist_geolocation_dataset.csv',
    'category_translation': 'product_category_name_translation.csv'
}

# 3. 循环读取并导入
print("开始导入数据...")
for table_name, file_name in files.items():
    try:
        df = pd.read_csv(file_name)
        df.to_sql(table_name, engine, index=False, if_exists='replace')
        print(f"✅ {table_name} 表导入成功，共 {len(df)} 行")
    except FileNotFoundError:
        print(f"❌ 找不到文件：{file_name}，请检查文件名是否写对")
    except Exception as e:
        print(f"❌ 导入 {table_name} 时出错：{e}")
print("导入完成！")

