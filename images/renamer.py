import os

for i in range(100):
    path = "C:\\Users\\miros\\Documents\\cat v3.0\\images\\cats\\"
    os.system(" ".join(["rename", f'"{path}{i}.jpg"', f'"{i}r.jpg"']))
