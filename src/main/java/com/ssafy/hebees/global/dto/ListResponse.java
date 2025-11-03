package com.ssafy.hebees.global.dto;

import java.util.List;

public record ListResponse<T>(
    List<T> data
) {

}
