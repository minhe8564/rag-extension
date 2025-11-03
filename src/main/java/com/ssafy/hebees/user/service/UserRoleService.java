package com.ssafy.hebees.user.service;

import com.ssafy.hebees.user.dto.request.UserRoleUpsertRequest;
import com.ssafy.hebees.user.entity.UserRole;

import java.util.List;
import java.util.UUID;

public interface UserRoleService {

    List<UserRole> getRoles();

    UserRole getRole(UUID userRoleNo);

    UserRole createRole(UserRoleUpsertRequest request);

    void deleteRole(UUID userRoleNo);

    UserRole updateRole(UUID userRoleNo, UserRoleUpsertRequest request);
}


