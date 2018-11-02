"""
jsonオブジェクトをjobインスタンスに詰め替えるトランスレータ
"""

flow_obj_cache = {} # uuid: Jsonオブジェクト
flows_cache = {} # uuid: Flowインスタンス

def make_job_from_uuid(flow_uuid):
    global flow_obj_cache
    global flows_cache
    flow_obj_cache = {}
    flows_cache = {}
    json_obj = load_flow_obj(flow_uuid)
    flow = make_flow(flow_uuid, json_obj)
    return make_job(json_obj, flow, {}, {}, {}, {})

def load_flow_obj(flow_uuid):
    if flow_uuid in flow_obj_cache:
        return flow_obj_cache[flow_uuid]

    flows_path = Path(os.environ['KENG_FLOWS_PATH']).joinpath(f'{flow_uuid}.json')
    with open(flows_path, 'r', encoding='utf-8') as fd:
        obj = json.loads(fd.read(), encoding='utf-8')
        flow_obj_cache[flow_uuid] = obj
        return obj

def make_job(json_obj, flow, args, srcs, dsts, inputs):
    # make step
    step = Step(flow, args, srcs, dsts)

    # make job
    job = Job(step, inputs)

    if step.is_flow:

        # make subjobs
        nodes = parse_nodes(json_obj)
        data = parse_data(json_obj)
        job.jobs = parse_subjobs(nodes, data)

        # make lasts
        job.lasts = parse_lasts(data, jobs)

    return job

def make_flow(flow_uuid, obj):

    # キャッシュをチェックする
    if flow_uuid in flows_cache:
        return flows_cache[flow_uuid]

    flow = Flow(flow_uuid)

    for param in obj['params']:
        flow.params.append(Parameter(param['name']))
    flow.i_ports = obj['ports'][0]
    flow.o_ports = obj['ports'][1]
    return flow

def parse_lasts(data, subjobs):
    src_values = {src for subjob in subjobs for src in subjob.step.srcs.values()}
    last_keys = data.keys() - src_values
    return {key: data[key] for key in last_keys}

def parse_data(obj):
    return {node['id']: parse_datum(node) for node in obj['nodes']
                                 if node['type'] == 'frame'}

def parse_datum(node_obj):
    frame_uuid = node_obj['uuid']
    if frame_uuid is not None:
        frames_path = os.environ['KENG_FRAMES_PATH']
        data_source = node_obj['dataSource']
        file_name = f'{frame_uuid}.{data_source}'
        source = PathFileSource(data_source, frames_path, file_name)
        datum = Frame(frame_uuid, source)
        datum.is_temp = False
    else:
        datum = Frame()
    return datum

def parse_nodes(obj):
    return [node for node in obj['nodes']
                 if node['type'] in ['command', 'flow']]

def parse_subjobs(nodes, data):
    return [parse_subjob(node, data) for node in nodes]

def parse_subjob(node, data):
    t = node['type']

    args = node['args']
    srcs = node['srcs']
    dsts = node['dsts']
    inputs = parse_job_inputs(data, srcs)
    if t == 'command':
        new_step = parse_command_step(node, args, srcs, dsts)
        new_job = Job(new_step, inputs)
    elif t == 'flow':
        flow_uuid = node['uuid']
        json_obj = load_flow_obj(flow_uuid)
        flow = make_flow(flow_uuid, json_obj)
        new_job = make_job(json_obj, flow, args, srcs, dsts, inputs)
    return new_job

def parse_job_inputs(data, srcs):
    return {v: data[v] for v in srcs.values()}

def parse_command_step(node_obj, args, srcs, dsts):
    return Step(commands[node_obj['commandId']], args, srcs, dsts)
