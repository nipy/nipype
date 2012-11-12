spm_metadata = ['field', 'mandatory', 'copyfile', 'xor', 'requires', 'usedefault']
cmd_metadata = ['argstr', 'mandatory', 'copyfile', 'xor', 'requires', 'usedefault',
                'sep', 'genfile', 'hash_files']
py_metadata = ['mandatory', 'copyfile', 'xor', 'requires', 'usedefault']

def create_spmtest_func(pkg, interface, object):
    cmd = ['def test_%s():'%interface.lower()]
    cmd += ["yield assert_equal, %s.%s._jobtype, '%s'"%(pkg, interface, object._jobtype)]
    cmd += ["yield assert_equal, %s.%s._jobname, '%s'"%(pkg, interface, object._jobname)]
    input_fields = ''
    for field, spec in object.inputs.items():
        input_fields += '%s = dict('%field
        for key, value in spec.__dict__.items():
            if key in spm_metadata:
                if key == 'field':
                    value = "'%s'"%value
                input_fields += "%s=%s,"%(key,str(value))
        input_fields += '),\n'
    cmd += ['input_map = dict(%s)'%input_fields]
    cmd += ['instance = %s.%s()'%(pkg, interface)]
    cmd += ["""
for key, metadata in input_map.items():
    for metakey, value in metadata.items():
        yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value"""]
    return cmd

def create_cmdtest_func(pkg, interface, object):
    cmd = ['def test_%s():'%interface.lower()]
    input_fields = ''
    for field, spec in object.inputs.items():
        input_fields += '%s = dict('%field
        for key, value in spec.__dict__.items():
            if key in cmd_metadata:
                if key == 'argstr':
                    value = "'%s'"%value
                input_fields += "%s=%s,"%(key,str(value))
        input_fields += '),\n'
    cmd += ['input_map = dict(%s)'%input_fields]
    cmd += ['\tinstance = %s.%s()'%(pkg, interface)]
    cmd += ["""\tfor key, metadata in input_map.items():
    for metakey, value in metadata.items():
        yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value"""]
    print '\n'.join(cmd)+'\n'

def create_pytest_func(pkg, interface, object):
    cmd = ['def test_%s():'%interface.lower()]
    input_fields = ''
    for field, spec in object.inputs.items():
        input_fields += '%s = dict('%field
        for key, value in spec.__dict__.items():
            if key in cmd_metadata:
                if key == 'argstr':
                    value = "'%s'"%value
                input_fields += "%s=%s,"%(key,str(value))
        input_fields += '),\n'
    cmd += ['input_map = dict(%s)'%input_fields]
    cmd += ['\tinstance = %s.%s()'%(pkg, interface)]
    cmd += ["""\tfor key, metadata in input_map.items():
    for metakey, value in metadata.items():
        yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value"""]
    print '\n'.join(cmd)+'\n'
