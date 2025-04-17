package com.raghavan.akshitma.github.shruti.utils

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MicrophoneHelper(private val activity: Activity) {

    private val microphonePermission = Manifest.permission.RECORD_AUDIO

    fun hasMicrophonePermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            activity,
            microphonePermission
        ) == PackageManager.PERMISSION_GRANTED
    }

    fun requestMicrophonePermission(requestCode: Int = 101) {
        if (!hasMicrophonePermission()) {
            ActivityCompat.requestPermissions(
                activity,
                arrayOf(microphonePermission),
                requestCode
            )
        }
    }

    fun handlePermissionResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
        onGranted: () -> Unit,
        onDenied: () -> Unit
    ) {
        if (requestCode == 101 && permissions.contains(microphonePermission)) {
            val resultIndex = permissions.indexOf(microphonePermission)
            if (grantResults[resultIndex] == PackageManager.PERMISSION_GRANTED) {
                onGranted()
            } else {
                onDenied()
            }
        }
    }
}
