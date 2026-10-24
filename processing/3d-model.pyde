import peasy.*
import java.net.*

PeasyCam cam
DatagramSocket udpSocket

float roll_target = 0, pitch_target = 0, yaw_target = 0
float lerp_speed = 0.05

float qw = 1, qx = 0, qy = 0, qz = 0
float tw = 1, tx = 0, ty = 0, tz = 0

PShape cansat
PVector modelCenter

void setup() {
    size(800, 600, P3D)
    cansat = loadShape("cansat.obj")
    modelCenter = getShapeCenter(cansat)
    cam = new PeasyCam(this, 500)
    try {
        udpSocket = new DatagramSocket(5005)
        udpSocket.setSoTimeout(1)
    } catch(Exception e) {
        println("UDP error: " + e.getMessage())
    }
}

PVector getShapeCenter(PShape s) {
    float minX = Float.MAX_VALUE, maxX = Float.MIN_VALUE
    float minY = Float.MAX_VALUE, maxY = Float.MIN_VALUE
    float minZ = Float.MAX_VALUE, maxZ = Float.MIN_VALUE

    if (s.getVertexCount() > 0) {
        for (int j=0
             j < s.getVertexCount()
             j++) {
            PVector v = s.getVertex(j)
            minX = min(minX, v.x)
            maxX = max(maxX, v.x)
            minY = min(minY, v.y)
            maxY = max(maxY, v.y)
            minZ = min(minZ, v.z)
            maxZ = max(maxZ, v.z)
        }
    } else {
        for (int i=0
             i < s.getChildCount()
             i++) {
            PShape child = s.getChild(i)
            for (int j=0
                 j < child.getVertexCount()
                 j++) {
                PVector v = child.getVertex(j)
                minX = min(minX, v.x)
                maxX = max(maxX, v.x)
                minY = min(minY, v.y)
                maxY = max(maxY, v.y)
                minZ = min(minZ, v.z)
                maxZ = max(maxZ, v.z)
            }
        }
    }

    println("X: " + minX + " to " + maxX)
    println("Y: " + minY + " to " + maxY)
    println("Z: " + minZ + " to " + maxZ)

    return new PVector(
        (minX + maxX) / 2,
        (minY + maxY) / 2,
        (minZ + maxZ) / 2
    )
}

void eulerToQuat(float roll_deg, float pitch_deg, float yaw_deg) {
    float r = radians(roll_deg) * 0.5
    float p = radians(pitch_deg) * 0.5
    float y = radians(yaw_deg) * 0.5

    float cr = cos(r), sr = sin(r)
    float cp = cos(p), sp = sin(p)
    float cy = cos(y), sy = sin(y)

    tw = cr*cp*cy + sr*sp*sy
    tx = sr*cp*cy - cr*sp*sy
    ty = cr*sp*cy + sr*cp*sy
    tz = cr*cp*sy - sr*sp*cy
}

void slerpQuat(float t) {
    float dot = qw*tw + qx*tx + qy*ty + qz*tz

    if (dot < 0) {
        tw = -tw
        tx = -tx
        ty = -ty
        tz = -tz
        dot = -dot
    }

    float s0, s1
    if (dot > 0.9995) {
        s0 = 1 - t
        s1 = t
    } else {
        float angle = acos(dot)
        float sinAngle = sin(angle)
        s0 = sin((1 - t) * angle) / sinAngle
        s1 = sin(t * angle) / sinAngle
    }

    qw = s0*qw + s1*tw
    qx = s0*qx + s1*tx
    qy = s0*qy + s1*ty
    qz = s0*qz + s1*tz

    float mag = sqrt(qw*qw + qx*qx + qy*qy + qz*qz)
    qw /= mag
    qx /= mag
    qy /= mag
    qz /= mag
}

void applyQuat() {
    float x2 = qx*qx, y2 = qy*qy, z2 = qz*qz
    float xy = qx*qy, xz = qx*qz, yz = qy*qz
    float wx = qw*qx, wy = qw*qy, wz = qw*qz

    applyMatrix(
        1-2*(y2+z2),  2*(xy-wz),    2*(xz+wy),   0,
        2*(xy+wz),    1-2*(x2+z2),  2*(yz-wx),   0,
        2*(xz-wy),    2*(yz+wx),    1-2*(x2+y2), 0,
        0,            0,            0,            1
    )
}

void draw() {
    background(30)
    lights()
    receiveUDP()

    drawAxes(200)

    slerpQuat(lerp_speed)
    applyQuat()
    drawCansat()

    cam.beginHUD()
    fill(255)
    textSize(14)
    text("Roll:  " + nf(roll_target,  1, 1) + "°", 10, 20)
    text("Pitch: " + nf(pitch_target, 1, 1) + "°", 10, 40)
    text("Yaw:   " + nf(yaw_target,   1, 1) + "°", 10, 60)
    cam.endHUD()
}

void drawCansat() {
    pushMatrix()
    noStroke()

    scale(0.5)
    translate(-modelCenter.x, -modelCenter.y, -modelCenter.z + 170)
    shape(cansat, 0, 0)
    popMatrix()
}

void drawAxes(float len) {
    pushMatrix()
    strokeWeight(2)
    stroke(255, 0, 0)
    line(0, 0, 0, len, 0, 0)
    // X rojo
    stroke(0, 255, 0)
    line(0, 0, 0, 0, len, 0)
    // Y verde
    stroke(0, 0, 255)
    line(0, 0, 0, 0, 0, len)
    // Z azul
    strokeWeight(1)
    popMatrix()
}

void receiveUDP() {
    try {
        byte[] buf = new byte[256]
        DatagramPacket packet = new DatagramPacket(buf, buf.length)
        udpSocket.receive(packet)
        String data = new String(packet.getData(), 0, packet.getLength()).trim()
        String[] parts = data.split(",")
        if (parts.length >= 3) {
            roll_target = float(parts[0])
            pitch_target = float(parts[1])
            yaw_target = float(parts[2])
            eulerToQuat(roll_target, pitch_target, yaw_target)
        }
    } catch(Exception e) {
        // no new data, keep interpolating
    }
}
