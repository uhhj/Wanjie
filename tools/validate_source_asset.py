import argparse,json
from rg_common import *
def main():
    p=argparse.ArgumentParser(description='Validate immutable frozen source against recorded hash. Never overwrite it.')
    p.parse_args()
    try:
        im=check_source(); a=np.array(im)[:,:,3]
        result={'status':'PASS','source':config()['source'],'sha256':sha(config()['source']),'dimensions':list(im.size),'rgba':im.mode=='RGBA','transparent_pixels':int((a==0).sum()),'alpha_extrema':[int(a.min()),int(a.max())],'timestamp':now()}
    except (ValueError,FileNotFoundError) as e: result={'status':'FAIL','reason':str(e),'timestamp':now()}
    write('reports/source_validation.json',result); print(json.dumps(result)); return 0 if result['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())

