#include <Python.h>

static PyMethodDef charidotella_extension_placeholder_methods[] = {{NULL, NULL, 0, NULL}};
static struct PyModuleDef charidotella_extension_placeholder_definition = {
    PyModuleDef_HEAD_INIT,
    "charidotella_extension_placeholder",
    "Placeholder to force Charidotella to build wheels for each platform",
    -1,
    charidotella_extension_placeholder_methods};
PyMODINIT_FUNC PyInit_charidotella_extension_placeholder() {
    return PyModule_Create(&charidotella_extension_placeholder_definition);
}
