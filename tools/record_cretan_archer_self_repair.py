"""Consolidate actual local part-edit provenance without claiming native masks."""
import json
from datetime import datetime,timezone
from PIL import Image
import cretan_archer_pipeline as p

def main():
    p.verify_frozen();records=[]
    mapping={'pelvis':'pelvis_under_near_hand','near_thigh':'leg_near_thigh_hidden_hip',
             'far_thigh':'leg_far_thigh_hidden_hip','torso':'torso_under_near_arm'}
    prompts=p.load(p.REPORT+'self_repair/body_ai_prompts.json')
    for entry in prompts:
        job=mapping[entry['part']];crop=p.load(p.WORK+'self_repair/body/'+job+'_crop.json')
        raw={'pelvis':'pelvis','near_thigh':'near_thigh','far_thigh':'far_thigh','torso':'torso'}[entry['part']]+'_generated_raw.png'
        path=p.WORK+'self_repair/body/'+raw
        im=Image.open(p.ROOT/path)
        record={**entry,'job_id':'self_repair_'+job,'model_call_executed':True,
          'input_file':crop['input'].replace('\\','/'),'reference_file':crop['reference'].replace('\\','/'),
          'mask_guidance_file':crop['mask'].replace('\\','/'),'crop_box':crop['crop'],
          'frozen_body_sha256':p.sha(p.BODY),'raw_output_file':path,'raw_output_sha256':p.sha(path),'raw_dimensions':list(im.size),
          'recorded_at':p.now(),'output_file_timestamp':datetime.fromtimestamp((p.ROOT/path).stat().st_mtime,timezone.utc).isoformat(),
          'timestamp_basis':'filesystem output receipt; exact remote model timestamp not exposed',
          'derived_patch_records':p.REPORT+'self_repair/body/repair_jobs.json'}
        for key in ['input_file','reference_file','mask_guidance_file']:record[key.replace('_file','_sha256')]=p.sha(record[key])
        records.append(record)
    p.save(p.REPORT+'self_repair/body/ai_jobs.json',records)
    print(json.dumps({'actual_body_part_calls':len(records),'separate_equipment_jobs':[
        p.REPORT+'self_repair/bow_arrow/bow_grip_ai_job.json',p.REPORT+'self_repair/bow_arrow/arrow_single_ai_job.json',
        p.REPORT+'self_repair/quiver_cloak/ai_jobs.json']}))
if __name__=='__main__':main()
