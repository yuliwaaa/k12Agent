class Dog:
    def __init__(self, name):
        self.name = name

    def bark(self):
        # self 就是调用这个方法的那个对象
        return f"{self.name} says woof!"


dog1 = Dog("Buddy")  # 创建对象1
dog2 = Dog("Max")  # 创建对象2

print(dog1.bark())  # self = dog1，输出：Buddy says woof!
print(dog2.bark())  # self = dog2，输出：Max says woof!