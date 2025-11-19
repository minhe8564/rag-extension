package com.ssafy.hebees.user.service;

import com.ssafy.hebees.user.dto.request.UserRoleUpsertRequest;
import com.ssafy.hebees.user.entity.UserRole;
import com.ssafy.hebees.user.repository.UserRepository;
import com.ssafy.hebees.user.repository.UserRoleRepository;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserRoleServiceImpl implements UserRoleService {

    private final UserRoleRepository userRoleRepository;
    private final UserRepository userRepository;

    @Override
    public List<UserRole> getRoles() {
        return userRoleRepository.findAll(Sort.by(Sort.Direction.ASC, "name"));
    }

    @Override
    public UserRole getRole(UUID userRoleNo) {
        return userRoleRepository.findById(userRoleNo)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_ROLE_NOT_FOUND));
    }

    @Override
    @Transactional
    public UserRole createRole(UserRoleUpsertRequest request) {
        if (userRoleRepository.existsByNameWithQueryDSL(request.name())) {
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        UserRole entity = request.toEntity();
        return userRoleRepository.save(entity);
    }

    @Override
    @Transactional
    public void deleteRole(UUID userRoleNo) {
        UserRole role = getRole(userRoleNo);

        if (userRepository.existsByRoleUuid(userRoleNo)) {
            throw new BusinessException(ErrorCode.USER_ROLE_IN_USE);
        }

        userRoleRepository.delete(role);
    }

    @Override
    @Transactional
    public UserRole updateRole(UUID userRoleNo, UserRoleUpsertRequest request) {
        UserRole role = getRole(userRoleNo);

        String requestedName = request.name();
        if (!role.getName().equals(requestedName)
            && userRoleRepository.existsByNameWithQueryDSL(requestedName)) {
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        role.update(request.mode(), requestedName);
        return role;
    }
}


