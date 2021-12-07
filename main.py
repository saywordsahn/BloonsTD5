import pygame, sys, os, time, math


scrwid = 800
scrhei = 600
squsize = 50
fps = 30

enemylist = []
towerlist = []
bulletlist = []
iconlist = []
senderlist = []

colors = {
    'yellow':   (255,255,0),
    'lime':     (0,255,0),
    'darkblue': (0,0,255),
    'aqua':     (0,255,255),
    'magenta':  (255,0,255),
    'purple':   (128,0,128),
    'green':    (97,144,0),
    'purple':   (197,125,190),
    'brown':    (110,73,32),}

def play_music(file, volume=1, loop=-1):
    pygame.mixer.music.load(file)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(loop)
   
def stop_music(): pygame.mixer.music.stop()

def imgLoad(file,size=None):
    image = pygame.image.load(file).convert_alpha()
    return pygame.transform.scale(image,size) if size else image

class Player:
    towers = [
        'dart monkey',
        'tack shooter',
        'sniper monkey',
        'boomerang thrower',
        'ninja monkey',
        'bomb tower',
        'ice tower',
        'glue gunner',
        'monkey buccaneer',
        'super monkey',
        'monkey apprentice',
        'spike factory',
        'road spikes',
        'exploding pineapple',]

    def __init__(self):
        self.health = 100
        self.money = 650

player = Player()


EnemyImageArray = dict()
TowerImageArray = dict()
def loadImages():
    for tower in player.towers: TowerImageArray[tower] = imgLoad('towers/'+tower+'.png')

    bloon = imgLoad('enemies/bloon.png')
    EnemyImageArray['red'] = bloon
    width,height = bloon.get_size()
    for name in colors:
        image = bloon.copy()
        for x in range(width):
            for y in range(height):
                p = image.get_at((x,y))[:-1]
                if p not in ((0,0,0),(255,255,255)):
                    c = colors[name]
                    r,g,b = p[0]*c[0]/255, p[0]*c[1]/255, p[0]*c[2]/255
                    image.set_at((x,y),(min(int(r),255),min(int(g),255),min(int(b),255)))
        EnemyImageArray[name] = image

def get_angle(a,b): return 180-(math.atan2(b[0]-a[0],b[1]-a[1]))/(math.pi/180)

class Map:
    def __init__(self):
        self.map = 'monkey lane'
        self.loadmap()

    def loadmap(self):
        self.targets = eval(open('maps/%s/targets.txt' % self.map,'r').read())
        self.waves = eval(open('maps/%s/waves.txt' % self.map,'r').read())

    def getmovelist(self):
        self.pathpoints = []
        for i in range(len(self.targets)-1):
            a,b = self.targets[i:i+2]
            self.pathpoints+=[0]

    def get_background(self):
        background = imgLoad('maps/%s/image.png' % self.map)
        background2 = imgLoad('maps/%s/image2.png' % self.map).convert_alpha()
        background3 = imgLoad('maps/%s/image3.png' % self.map).convert_alpha()
        for i in range(len(self.targets)-1): pygame.draw.line(background,(0,0,0),self.targets[i],self.targets[i+1])
        return background,background2,background3

mapvar = Map()



class Enemy:
    layers = [ # Name Health Speed CashPrize
        ('red',      10, 1, 10000),
        ('darkblue', 11, 1.0, 0),
        ('green',    12, 1.2, 0),
        ('yellow',   13, 2.0, 0),]

    def __init__(self,layer):
        self.layer = layer
        self.setlayer()

        self.targets = mapvar.targets
        self.pos = list(self.targets[0])
        self.target = 0
        self.next_target()
        self.rect = self.image.get_rect(center=self.pos)
        self.distance = 0

        enemylist.append(self)

    def setlayer(self): self.name,self.health,self.speed,self.cashprize = self.layers[self.layer]; self.image = EnemyImageArray[self.name]
    def nextlayer(self): self.layer-=1; self.setlayer()

    def next_target(self):
        if self.target<len(self.targets)-1:
            self.target+=1; t=self.targets[self.target]; self.angle = 180-(math.atan2(t[0]-self.pos[0],t[1]-self.pos[1]))/(math.pi/180)
            self.vx,self.vy = math.sin(math.radians(self.angle)),-math.cos(math.radians(self.angle))
        else: self.kill(); player.health-=self.layer+1

    def hit(self,damage):
        player.money+=1
        self.health -= damage
        if self.health<=0:
            player.money+=self.cashprize
            self.nextlayer() if self.layer>0 else self.kill()

    def kill(self): enemylist.remove(self)

    def move(self,frametime):
        speed = frametime*fps*self.speed
        a,b = self.pos,self.targets[self.target]
        
        a[0] += self.vx*speed
        a[1] += self.vy*speed
        
        if (b[0]-a[0])**2+(b[1]-a[1])**2<=speed**2: self.next_target()
        self.rect.center = self.pos
        self.distance+=speed

class Tower:
    def __init__(self,pos):
        self.targetTimer = 0
        self.rect = self.image.get_rect(center=pos)
        towerlist.append(self)

    def takeTurn(self,frametime,screen):
        self.startTargetTimer = self.firerate
        self.targetTimer -= frametime
        if self.targetTimer<=0:
            enemypoint = self.target()
            if enemypoint:
                pygame.draw.line(screen,(255,255,255),self.rect.center,enemypoint)
                self.targetTimer=self.startTargetTimer
    def target(self):
        for enemy in sorted(enemylist,key=lambda i: i.distance,reverse=True):
            if (self.rect.centerx-enemy.rect.centerx)**2+(self.rect.centery-enemy.rect.centery)**2<=self.rangesq:
                self.angle = int(get_angle(self.rect.center,enemy.rect.center))
                self.image = pygame.transform.rotate(self.imagecopy,-self.angle)
                self.rect = self.image.get_rect(center=self.rect.center)
                enemy.hit(self.damage)
                return enemy.rect.center

class createTower(Tower):
    def __init__(self,tower,pos,info):
        self.tower = tower
        self.cost,self.firerate,self.range,self.damage = info
        self.rangesq = self.range**2
        
        self.image = TowerImageArray[tower]
        self.imagecopy = self.image.copy()
        self.angle = 0
        Tower.__init__(self,pos)

class Icon:
    towers = { # Cost FireRate Range Damage
        'dart monkey'         : [ 215, 1.0, 100, 1],
        'tack shooter'        : [ 390, 1.0, 40, 1],
        'sniper monkey'       : [ 0, 0.0, 2000, 10000],
        'boomerang thrower'   : [ 430, 1.0, 40, 1],
        'ninja monkey'        : [ 650, 1.0, 40, 1],
        'bomb tower'          : [ 700, 1.0, 40, 1],
        'ice tower'           : [ 410, 1.0, 40, 1],
        'glue gunner'         : [ 325, 1.0, 40, 1],
        'monkey buccaneer'    : [ 650, 1.0, 40, 1],
        'super monkey'        : [4320, 1.0, 40, 1],
        'monkey apprentice'   : [ 595, 1.0, 40, 1],
        'spike factory'       : [ 755, 1.0, 40, 1],
        'road spikes'         : [  30, 1.0, 40, 1],
        'exploding pineapple' : [  25, 1.0, 40, 1],}

    def __init__(self,tower):
        self.tower = tower
        self.cost,self.firerate,self.range,self.damage = self.towers[tower]
        iconlist.append(self)
        self.img = pygame.transform.scale(TowerImageArray[tower],(41,41))
        i = player.towers.index(tower); x,y = i%2,i//2
        self.rect = self.img.get_rect(x=700+x*(41+6)+6,y=100+y*(41+6)+6)


def dispText(screen,wavenum):
    font = pygame.font.SysFont('arial', 18)
    # font = pygame.font.Font('C:/Windows/Fonts/ARCHRISTY.ttf',18)
    h = font.get_height()+2
    strings = [('Round: %d/%d' % (wavenum,len(mapvar.waves)),(200,20)),
               (str(player.money),(730,15)),
               (str(max(player.health,0)),(730,45))]
    for string,pos in strings:
        text = font.render(string,2,(0,0,0))
        screen.blit(text,text.get_rect(midleft=pos))

def drawTower(screen,tower,selected):
    screen.blit(tower.image,tower.rect)
    if tower==selected:
        rn = tower.range
        surface = pygame.Surface((2*rn,2*rn)).convert_alpha(); surface.fill((0,0,0,0))
        pygame.draw.circle(surface,(0,255,0,85),(rn,rn),rn)
        screen.blit(surface,tower.rect.move((-1*rn,-1*rn)).center)
    elif tower.rect.collidepoint(pygame.mouse.get_pos()):
        rn = tower.range
        surface = pygame.Surface((2*rn,2*rn)).convert_alpha(); surface.fill((0,0,0,0))
        pygame.draw.circle(surface,(255,255,255,85),(rn,rn),rn)
        screen.blit(surface,tower.rect.move((-1*rn,-1*rn)).center)

def selectedIcon(screen,selected):
    mpos = pygame.mouse.get_pos()
    image = TowerImageArray[selected.tower]
    rect = image.get_rect(center=mpos)
    screen.blit(image,rect)

    collide = False
    rn = selected.range
    surface = pygame.Surface((2*rn,2*rn)).convert_alpha(); surface.fill((0,0,0,0))
    pygame.draw.circle(surface,(255,0,0,75) if collide else (0,0,255,75),(rn,rn),rn)
    screen.blit(surface,surface.get_rect(center=mpos))

def selectedTower(screen,selected,mousepos):
    selected.genButtons(screen)
    for img,rect,info,infopos,cb in selected.buttonlist:
        screen.blit(img,rect)
        if rect.collidepoint(mousepos): screen.blit(info,infopos)

def drawIcon(screen,icon,mpos,font):
    screen.blit(icon.img,icon.rect)
    if icon.rect.collidepoint(mpos):
        text = font.render("%s Tower (%d)" % (icon.tower,icon.cost),2,(0,0,0))
        textpos = text.get_rect(right=700-6,centery=icon.rect.centery)
        screen.blit(text,textpos)

class Sender:
    def __init__(self,wave):
        self.wave = wave; self.timer = 0; self.rate = 1
        self.enemies = []; enemies = mapvar.waves[wave-1].split(',')
        for enemy in enemies:
            amount,layer = enemy.split('*')
            self.enemies += [eval(layer)-1]*eval(amount)
        senderlist.append(self)

    def update(self,frametime,wave):
        if not self.enemies:
            if not enemylist: senderlist.remove(self); wave+=1; player.money+=99+self.wave
        elif self.timer>0: self.timer -= frametime
        else: self.timer = self.rate; Enemy(self.enemies[0]); del self.enemies[0]
        return wave

def workEvents(selected,wave,speed):
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3: selected = None
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

            if selected in towerlist: selected = None
            elif selected in iconlist:
                if player.money>=selected.cost:
                    rect = selected.img.get_rect(center=event.pos)
                    collide = False
                    if not collide: player.money-=selected.cost; selected = createTower(selected.tower,event.pos,selected.towers[selected.tower])

            for obj in iconlist + (towerlist if not selected else []):
                if obj.rect.collidepoint(event.pos): selected = obj; break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not enemylist:
                if wave<=len(mapvar.waves): Sender(wave)
                else: print('No more rounds! Soz... :(')

            if event.key == pygame.K_k and selected in towerlist: player.money+=int(selected.cost*0.9); towerlist.remove(selected); selected = None
            if event.key == pygame.K_w and speed<10: speed+=1
            if event.key == pygame.K_s and speed>1: speed-=1
    return selected,wave,speed



def main():
    pygame.init()
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption('Bloons Tower Defence')
    screen = pygame.display.set_mode((scrwid,scrhei))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None,20)

    mapvar.getmovelist()

    background = pygame.Surface((800,600)); background.set_colorkey((0,0,0))
    heart,money,plank = imgLoad('images/heart.png'), imgLoad('images/money.png'), imgLoad('images/plank.png')
    w,h = plank.get_size()
    for y in range(scrhei//h): background.blit(plank,(scrwid-w,y*h))
    for y in range(3):
        for x in range(scrwid//w): background.blit(plank,(x*w,scrhei-(y+1)*h))
    background.blit(money,(scrwid-w+6,h//2-money.get_height()//2))
    background.blit(heart,(scrwid-w+6,h+h//2-heart.get_height()//2))


    
    level_img,t1,t2 = mapvar.get_background()
    loadImages()
    for tower in player.towers: Icon(tower)
    selected = None
    speed = 3
    wave = 1
    play_music('music/maintheme.mp3')

    while True:
        starttime = time.time()
        clock.tick(fps)
        frametime = (time.time()-starttime)*speed
        screen.blit(level_img,(0,0))
        mpos = pygame.mouse.get_pos()

        if senderlist: wave = senderlist[0].update(frametime,wave)

        z0,z1 = [],[]
        for enemy in enemylist:
            d = enemy.distance
            if d<580: z1+=[enemy]
            elif d<950: z0+=[enemy]
            elif d<2392: z1+=[enemy]
            elif d<2580: z0+=[enemy]
            else: z0+=[enemy]

        for enemy in z0: enemy.move(frametime); screen.blit(enemy.image,enemy.rect)
        screen.blit(t1,(0,0))
        screen.blit(t2,(0,0))
        for enemy in z1: enemy.move(frametime); screen.blit(enemy.image,enemy.rect)

        for tower in towerlist: tower.takeTurn(frametime,screen); drawTower(screen,tower,selected)


        screen.blit(background,(0,0))

        for icon in iconlist: drawIcon(screen,icon,mpos,font)
        selected,wave,speed = workEvents(selected,wave,speed)
        if selected and selected.__class__ == Icon: selectedIcon(screen,selected)
        dispText(screen,wave)

        pygame.display.flip()



if __name__ == '__main__':
    main()




