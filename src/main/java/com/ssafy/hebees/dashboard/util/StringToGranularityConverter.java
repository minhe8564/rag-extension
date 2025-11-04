package com.ssafy.hebees.dashboard.util;

import com.ssafy.hebees.dashboard.dto.Granularity;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

@Component
public class StringToGranularityConverter implements Converter<String, Granularity> {

    @Override
    public Granularity convert(String source) {
        return source == null ? null : Granularity.from(source); // 앞서 만든 from(String)
    }
}
