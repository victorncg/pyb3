

# retorna os metodos de um objeto
def metodos(obj):
    return [i for i in dir(obj) if '__' not in i and callable(getattr(obj, i))]
 
# retorna os atributos de um objeto
def atributos(obj):
    return [i for i in dir(obj) if '__' not in i and not callable(getattr(obj, i))]






