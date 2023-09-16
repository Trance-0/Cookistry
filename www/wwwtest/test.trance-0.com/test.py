import random
print("Conda environment initialized!")
def generateRandomString(length = 10):
    characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%^!&-+=()'   
    n=len(characters)
    res=''
    for _ in range(length):
        res+=characters[random.randint(0,n)]
    return res
print(generateRandomString(16))
