
def foo(bar):
    print bar

num = 123

print num
import bugbuzz; bugbuzz.set_trace()
#import pdb; pdb.set_trace()

foo('xxx')
print num * 10
