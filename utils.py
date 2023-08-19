def process_array(array):
    s = ''.join(array)
    s = s.strip("{}")
    return [x.strip('"') for x in s.split(",")]