from app import add

i = 0
while True:
    add.delay(4, 5)
    add.delay(10, 20)
    add.delay(100, 20)
    i += 1
    if i == 10000:
        break
