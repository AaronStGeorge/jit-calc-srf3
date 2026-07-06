#pragma once
#include <cstddef>

struct hsaco_entry {
    const char * name;
    const unsigned char * data;
    size_t size;
};

const hsaco_entry * hsaco_catalog_find(const char * name);
