#version 310 es
precision mediump float;
float massive_array[65536][65536];
void main() {
    gl_Position = vec4(massive_array[0][0]);
}
