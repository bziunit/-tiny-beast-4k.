
import os,json,urllib.request

U=os.environ["MAKEFUN_ENV_URL"].rstrip("/")
def post(path,data={}):
 r=urllib.request.Request(U+path,json.dumps(data).encode(),{"Content-Type":"application/json"})
 return json.loads(urllib.request.urlopen(r,timeout=9).read())

V={"p":100,"n":320,"b":330,"r":500,"q":900,"k":0}

def choose(fen,moves):
 a,turn,castle,ep,*_=fen.split()
 b=[]
 for row in a.split("/"):
  for c in row:
   b += ["."]*int(c) if c.isdigit() else [c]
 def val(x):
  if x=="." : return 0
  v=V[x.lower()]
  return v if x.isupper() else -v
 def score(m):
  x,y=m[:2],m[2:4]
  i=ord(x[0])-97+(8-int(x[1]))*8
  j=ord(y[0])-97+(8-int(y[1]))*8
  p=b[i]; q=b[j]; s=0
  side=1 if turn=="w" else -1
  z=b[:]; z[j]=p; z[i]="."
  if p.lower()=="p" and x[0]!=y[0] and q==".":
   z[i//8*8+(j%8)]="."
  if p.lower()=="k" and abs(i-j)==2:
   if j>i:
    z[j-1]=z[j+1]; z[j+1]="."
   else:
    z[j+1]=z[j-2]; z[j-2]="."
  if len(m)>4:
   z[j]=m[4].upper() if side==1 else m[4]
  s=sum(val(c) for c in z)*side
  for k,c in enumerate(z):
   if c=="." : continue
   r,col=divmod(k,8)
   center=7-(abs(3.5-r)+abs(3.5-col))
   adv=(6-r if c.isupper() else r-1) if c.lower()=="p" else 0
   s+=side*(1 if c.isupper() else -1)*(center*2+adv*3)
  if q!=".":
   s+=V[q.lower()]*0.8
  if p.lower()=="q" and sum(1 for c in b if c.lower()=="q")>0:
   s-=8
  return s
 return max(moves,key=score)

while True:
 g=post("/game")
 if g.get("status")=="done":
  break
 while g.get("status")=="your_move":
  m=choose(g["fen"],g["legal_moves"])
  g=post("/move",{"game":g["game"],"move":m})
