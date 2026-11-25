import urllib.request
import json
import os
from pathlib import Path

base_url = 'http://localhost:8000'
ROOT_DIR = Path(__file__).resolve().parent.parent

def run_tests():
    tmp_id = 'scene_test_suite_tmp'
    try:
        print('1. Creating isolated test workspace via POST /api/scene/{id}/object (table)...')
        table_payload = {
            'id': 'test_table_1',
            'name': 'Test Oak Table',
            'category': 'table',
            'position': {'x': 0.0, 'y': 0.375, 'z': 0.0},
            'rotation': {'yaw': 0.0},
            'dimensions': {'width': 1.2, 'height': 0.75, 'depth': 0.8},
            'color': '#8c6954',
            'parts': [
                {'name': 'oak_top', 'shape': 'box', 'args': [1.2, 0.04, 0.8], 'position': [0.0, 0.73, 0.0], 'color': '#8c6954'}
            ]
        }
        req = urllib.request.Request(
            f'{base_url}/api/scene/{tmp_id}/object',
            data=json.dumps(table_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as resp:
            created = json.loads(resp.read().decode())
            assert created['scene_id'] == tmp_id
            assert len(created['objects']) == 1
            print(f'   Success: Created isolated scene {tmp_id} with custom parts preserved.')

        print('2. Testing GET /api/scenes & /api/scene/{id}...')
        with urllib.request.urlopen(f'{base_url}/api/scenes') as resp:
            scenes = json.loads(resp.read().decode())
            assert len(scenes) > 0, 'No scenes found'
        with urllib.request.urlopen(f'{base_url}/api/scene/{tmp_id}') as resp:
            scene = json.loads(resp.read().decode())
            print(f'   Success: Listed {len(scenes)} scenes and fetched {scene["scene_id"]}.')

        print('3. Testing GET /api/physical_clicks/config & /api/engine...')
        with urllib.request.urlopen(f'{base_url}/api/physical_clicks/config') as resp:
            cfg = json.loads(resp.read().decode())
            assert 'antigravity' in cfg.get('presets', {}), 'Missing antigravity preset'
        with urllib.request.urlopen(f'{base_url}/api/engine') as resp:
            eng = json.loads(resp.read().decode())
            print(f'   Success: Presets={list(cfg["presets"].keys())}, active engine={eng.get("engine")}.')

        first_id = tmp_id

        print('5. Testing CAD Prompt Edit: "place a phone on table"...')
        prompt_data = json.dumps({'prompt': 'place a phone on table'}).encode('utf-8')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/prompt', data=prompt_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            res_scene = json.loads(resp.read().decode())
            phone = res_scene['objects'][-1]
            assert 'phone' in phone['category'] or 'phone' in phone['name'].lower(), 'Last object should be phone'
            print(f'   Success: Phone created with id={phone["id"]}, attached_to_id={phone.get("attached_to_id")}')
            assert phone.get('attached_to_id') is not None, 'New phone should be attached to table'

        print('6. Testing CAD Prompt Edit: "unstick all"...')
        unstick_data = json.dumps({'prompt': 'unstick all'}).encode('utf-8')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/prompt', data=unstick_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            res_scene = json.loads(resp.read().decode())
            attached_count = sum(1 for o in res_scene['objects'] if o.get('attached_to_id'))
            print(f'   Success: Unstick all verified. Remaining attached objects = {attached_count}')
            assert attached_count == 0

        print('7. Testing CAD Prompt Edit: "stick phone to table"...')
        stick_data = json.dumps({'prompt': 'stick phone to table'}).encode('utf-8')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/prompt', data=stick_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            res_scene = json.loads(resp.read().decode())
            phone = next((o for o in res_scene['objects'] if o.get('attached_to_id') and ('phone' in o['category'] or 'phone' in o['name'].lower())), None)
            assert phone is not None, 'A phone object should be attached to table'
            print(f'   Success: Sticking verified. Phone ({phone["id"]}) attached to {phone.get("attached_to_id")}')

        print('8. Testing Transform Propagation on parent table move...')
        table_id = phone.get('attached_to_id')
        table_obj = next(o for o in res_scene['objects'] if o['id'] == table_id)
        initial_phone_x = phone['position']['x']
        new_table_pos = {'x': table_obj['position']['x'] + 0.4, 'y': table_obj['position']['y'], 'z': table_obj['position']['z']}
        update_data = json.dumps({'position': new_table_pos}).encode('utf-8')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/object/{table_id}', data=update_data, headers={'Content-Type': 'application/json'}, method='PUT')
        with urllib.request.urlopen(req) as resp:
            updated_scene = json.loads(resp.read().decode())
            updated_phone = next(o for o in updated_scene['objects'] if o['id'] == phone['id'])
            diff_x = round(updated_phone['position']['x'] - initial_phone_x, 3)
            print(f'   Success: Table moved +0.4m -> Phone automatically translated by {diff_x}m!')
            assert abs(diff_x - 0.4) < 0.001

        print('9. Testing Detach via PUT /api/scene/{id}/object/{obj_id} with attached_to_id="none"...')
        detach_data = json.dumps({'attached_to_id': 'none'}).encode('utf-8')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/object/{phone["id"]}', data=detach_data, headers={'Content-Type': 'application/json'}, method='PUT')
        with urllib.request.urlopen(req) as resp:
            detached_scene = json.loads(resp.read().decode())
            detached_phone = next(o for o in detached_scene['objects'] if o['id'] == phone['id'])
            print(f'   Success: Detachment verified. attached_to_id={detached_phone.get("attached_to_id")}')
            assert detached_phone.get('attached_to_id') is None

        print('10. Testing static endpoints: /qr.png and /assets/...')
        req = urllib.request.Request(f'{base_url}/qr.png')
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            print('   Success: /qr.png returned 200 OK')

        print('11. Testing GET /api/scene/{id}/antigravity_plan...')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/antigravity_plan')
        with urllib.request.urlopen(req) as resp:
            plan_data = json.loads(resp.read().decode())
            plan = plan_data.get('plan', [])
            assert len(plan) > 0, 'Plan should contain steps'
            first_step = plan[0]
            assert 'antigravity_prompt' in first_step, 'Step should have Antigravity prompt'
            print(f'   Success: Antigravity plan generated with {len(plan)} prioritized objects!')

        print(f'12. Testing GET /api/scene/{{id}}/object/{phone["id"]}/antigravity_prompt...')
        req = urllib.request.Request(f'{base_url}/api/scene/{first_id}/object/{phone["id"]}/antigravity_prompt')
        with urllib.request.urlopen(req) as resp:
            prompt_res = json.loads(resp.read().decode())
            prompt_txt = prompt_res.get('prompt', '')
            assert 'Antigravity' in prompt_txt, 'Prompt should reference Antigravity'
            assert phone['id'] in prompt_txt, 'Prompt should include object ID'
            print(f'   Success: Antigravity object prompt verified ({len(prompt_txt)} chars)!')

        print('\n[ALL TESTS PASSED WITH 100% SUCCESS]')
    finally:
        tmp_file = ROOT_DIR / 'backend' / 'storage' / 'scenes' / f'{tmp_id}.json'
        if tmp_file.exists():
            os.remove(tmp_file)

if __name__ == '__main__':
    run_tests()
