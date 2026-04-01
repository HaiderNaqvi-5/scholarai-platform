"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/auth-provider";
import { AppShell } from "@/components/layout/app-shell";
import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState, FeedbackNotice } from "@/components/ui/feedback-state";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { Capability, hasCapability } from "@/lib/authorization";
import { apiRequest } from "@/lib/api";
import type {
  ApiError,
  CurationRecordDetail,
  CurationRecordListResponse,
  CurationRawImportRequest,
  CurationRecordState,
  IngestionRunBulkRetryRequest,
  IngestionRunBulkRetryResponse,
  IngestionExecutionMode,
  IngestionRunDetail,
  IngestionRunListResponse,
  IngestionRunQueueAssignmentRequest,
  IngestionRunRetryRequest,
  IngestionRunStartRequest,
  IngestionRunSummary,
} from "@/lib/types";

const FILTERS: CurationRecordState[] = [
  "raw",
  "validated",
  "published",
  "archived",
];

const CURATION_SOURCE_OPTIONS = [
  {
    label: "UBC Graduate Funding",
    source_key: "ubc-grad-funding",
    source_display_name: "UBC Graduate Funding",
    source_base_url: "https://www.grad.ubc.ca/awards",
    source_type: "official",
  },
  {
    label: "Waterloo Graduate Funding",
    source_key: "waterloo-awards",
    source_display_name: "University of Waterloo Graduate Funding",
    source_base_url:
      "https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/funding",
    source_type: "official",
  },
  {
    label: "Fulbright Foreign Student",
    source_key: "fulbright-foreign-student",
    source_display_name: "Fulbright Foreign Student Program",
    source_base_url: "https://foreign.fulbrightonline.org",
    source_type: "official",
  },
] as const;

type CurationState = {
  isLoading: boolean;
  isDetailLoading: boolean;
  isRunsLoading: boolean;
  isSaving: boolean;
  activeAction: "save" | "import" | "ingestion" | "transition" | null;
  error: string | null;
  errorContext: "records" | "runs" | "detail" | "action" | null;
  actionFeedback:
    | {
        variant: "error" | "success";
        message: string;
      }
    | null;
  filter: CurationRecordState;
  records: CurationRecordListResponse["items"];
  selectedRecord: CurationRecordDetail | null;
  runs: IngestionRunSummary[];
  selectedRun: IngestionRunDetail | null;
};

type EditState = {
  title: string;
  provider_name: string;
  country_code: string;
  summary: string;
  funding_summary: string;
  field_tags: string;
  degree_levels: string;
  citizenship_rules: string;
  min_gpa_value: string;
  review_notes: string;
};

type ImportState = {
  source_key: string;
  source_display_name: string;
  source_base_url: string;
  source_url: string;
  title: string;
  provider_name: string;
  country_code: string;
  summary: string;
  field_tags: string;
  degree_levels: string;
  review_notes: string;
};

type IngestionState = {
  source_key: string;
  source_display_name: string;
  source_base_url: string;
  source_type: string;
  max_records: string;
  execution_mode: IngestionExecutionMode;
};

type RunFilterState = {
  status: "all" | "queued" | "running" | "completed" | "partial" | "failed";
  source_key: string;
  dispatch_status: string;
};

type IngestionBulkState = {
  selectedRunIds: string[];
  queueKey: string;
  queueNote: string;
};

const EMPTY_EDIT_STATE: EditState = {
  title: "",
  provider_name: "",
  country_code: "",
  summary: "",
  funding_summary: "",
  field_tags: "",
  degree_levels: "",
  citizenship_rules: "",
  min_gpa_value: "",
  review_notes: "",
};

const EMPTY_IMPORT_STATE: ImportState = {
  source_key: "manual_demo_import",
  source_display_name: "Manual demo import",
  source_base_url: "https://example.edu",
  source_url: "",
  title: "",
  provider_name: "",
  country_code: "CA",
  summary: "",
  field_tags: "data science",
  degree_levels: "MS",
  review_notes: "",
};

const EMPTY_INGESTION_STATE: IngestionState = {
  source_key: CURATION_SOURCE_OPTIONS[0].source_key,
  source_display_name: CURATION_SOURCE_OPTIONS[0].source_display_name,
  source_base_url: CURATION_SOURCE_OPTIONS[0].source_base_url,
  source_type: CURATION_SOURCE_OPTIONS[0].source_type,
  max_records: "5",
  execution_mode: "auto",
};

const EMPTY_RUN_FILTER_STATE: RunFilterState = {
  status: "all",
  source_key: "",
  dispatch_status: "",
};

const EMPTY_INGESTION_BULK_STATE: IngestionBulkState = {
  selectedRunIds: [],
  queueKey: "manual-review",
  queueNote: "",
};

export function CurationDashboardShell() {
  const { accessToken, currentUser } = useAuth();
  const canRunIngestion = hasCapability(
    currentUser,
    accessToken,
    Capability.CurationIngestionRun,
  );
  const canImportRaw = hasCapability(
    currentUser,
    accessToken,
    Capability.CurationImportWrite,
  );
  const canEditRecord = hasCapability(
    currentUser,
    accessToken,
    Capability.CurationRecordEdit,
  );
  const canTransitionRecord = hasCapability(
    currentUser,
    accessToken,
    Capability.CurationRecordTransition,
  );
  const [state, setState] = useState<CurationState>({
    isLoading: true,
    isDetailLoading: false,
    isRunsLoading: true,
    isSaving: false,
    activeAction: null,
    error: null,
    errorContext: null,
    actionFeedback: null,
    filter: "raw",
    records: [],
    selectedRecord: null,
    runs: [],
    selectedRun: null,
  });
  const [editState, setEditState] = useState<EditState>(EMPTY_EDIT_STATE);
  const [importState, setImportState] = useState<ImportState>(EMPTY_IMPORT_STATE);
  const [ingestionState, setIngestionState] =
    useState<IngestionState>(EMPTY_INGESTION_STATE);
  const [runFilterState, setRunFilterState] = useState<RunFilterState>(
    EMPTY_RUN_FILTER_STATE,
  );
  const [ingestionBulkState, setIngestionBulkState] = useState<IngestionBulkState>(
    EMPTY_INGESTION_BULK_STATE,
  );

  const loadRuns = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setState((current) => ({
      ...current,
      isRunsLoading: true,
      error: null,
      errorContext: null,
    }));
    try {
      const search = new URLSearchParams();
      search.set("page", "1");
      search.set("page_size", "8");
      if (runFilterState.status !== "all") {
        search.set("status", runFilterState.status);
      }
      if (runFilterState.source_key.trim()) {
        search.set("source_key", runFilterState.source_key.trim());
      }
      if (runFilterState.dispatch_status.trim()) {
        search.set("dispatch_status", runFilterState.dispatch_status.trim());
      }
      const response = await apiRequest<IngestionRunListResponse>(
        `/curation/ingestion-runs?${search.toString()}`,
        { token: accessToken },
      );

      setState((current) => ({
        ...current,
        isRunsLoading: false,
        runs: response.items,
      }));

      if (response.items[0]) {
        const detail = await apiRequest<IngestionRunDetail>(
          `/curation/ingestion-runs/${response.items[0].run_id}`,
          { token: accessToken },
        );
        setState((current) => ({ ...current, selectedRun: detail }));
      } else {
        setState((current) => ({ ...current, selectedRun: null }));
      }
    } catch (error) {
      setState((current) => ({
        ...current,
        isRunsLoading: false,
        error: resolveErrorMessage(error),
        errorContext: "runs",
      }));
    }
  }, [accessToken, runFilterState]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    let isActive = true;

    const loadRecords = async () => {
      setState((current) => ({
        ...current,
        isLoading: true,
        error: null,
        errorContext: null,
        selectedRecord: null,
      }));

      try {
        const response = await apiRequest<CurationRecordListResponse>(
          `/curation/records?state=${state.filter}`,
          { token: accessToken },
        );
        if (!isActive) {
          return;
        }

        setState((current) => ({
          ...current,
          isLoading: false,
          records: response.items,
        }));

        if (response.items[0]) {
          void loadRecordDetail(response.items[0].record_id, true);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          isLoading: false,
          records: [],
          error: resolveErrorMessage(error),
          errorContext: "records",
        }));
      }
    };

    const loadRecordDetail = async (recordId: string, initial = false) => {
      setState((current) => ({
        ...current,
        isDetailLoading: !initial,
        error: null,
        errorContext: null,
      }));
      try {
        const detail = await apiRequest<CurationRecordDetail>(
          `/curation/records/${recordId}`,
          { token: accessToken },
        );
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          isDetailLoading: false,
          selectedRecord: detail,
        }));
        setEditState(buildEditState(detail));
      } catch (error) {
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          isDetailLoading: false,
          error: resolveErrorMessage(error),
          errorContext: "detail",
        }));
      }
    };

    void loadRecords();

    return () => {
      isActive = false;
    };
  }, [accessToken, state.filter]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void loadRuns();
  }, [accessToken, loadRuns]);

  const selectedId = state.selectedRecord?.record_id ?? null;

  const actionButtons = useMemo(() => {
    if (!state.selectedRecord) {
      return [];
    }

    if (state.selectedRecord.record_state === "raw") {
      return [
        { label: "Approve", action: "approve", variant: "auth-link--primary" },
        { label: "Reject", action: "reject", variant: "auth-link--secondary" },
      ];
    }

    if (state.selectedRecord.record_state === "validated") {
      return [
        { label: "Publish", action: "publish", variant: "auth-link--primary" },
        { label: "Reject", action: "reject", variant: "auth-link--secondary" },
      ];
    }

    if (state.selectedRecord.record_state === "published") {
      return [
        { label: "Unpublish", action: "unpublish", variant: "auth-link--secondary" },
      ];
    }

    return [];
  }, [state.selectedRecord]);

  const refreshCurrentFilter = async (
    targetRecordId?: string,
    filterOverride?: CurationRecordState,
  ) => {
    if (!accessToken) {
      return;
    }

    const activeFilter = filterOverride ?? state.filter;
    setState((current) => ({
      ...current,
      isLoading: true,
      error: null,
      errorContext: null,
    }));
    try {
      const response = await apiRequest<CurationRecordListResponse>(
        `/curation/records?state=${activeFilter}`,
        { token: accessToken },
      );
      setState((current) => ({
        ...current,
        isLoading: false,
        filter: activeFilter,
        records: response.items,
      }));

      const nextRecordId = targetRecordId ?? response.items[0]?.record_id;
      if (nextRecordId) {
        const detail = await apiRequest<CurationRecordDetail>(
          `/curation/records/${nextRecordId}`,
          { token: accessToken },
        );
        setState((current) => ({
          ...current,
          selectedRecord: detail,
          isDetailLoading: false,
        }));
        setEditState(buildEditState(detail));
      } else {
        setState((current) => ({ ...current, selectedRecord: null }));
        setEditState(EMPTY_EDIT_STATE);
      }
    } catch (error) {
      setState((current) => ({
        ...current,
        isLoading: false,
        error: resolveErrorMessage(error),
        errorContext: "records",
      }));
    }
  };

  const loadRecord = async (recordId: string) => {
    if (!accessToken) {
      return;
    }

    setState((current) => ({
      ...current,
      isDetailLoading: true,
      error: null,
      errorContext: null,
    }));
    try {
      const detail = await apiRequest<CurationRecordDetail>(`/curation/records/${recordId}`, {
        token: accessToken,
      });
      setState((current) => ({
        ...current,
        isDetailLoading: false,
        selectedRecord: detail,
      }));
      setEditState(buildEditState(detail));
    } catch (error) {
      setState((current) => ({
        ...current,
        isDetailLoading: false,
        error: resolveErrorMessage(error),
        errorContext: "detail",
      }));
    }
  };

  const loadIngestionRun = async (runId: string) => {
    if (!accessToken) {
      return;
    }

    setState((current) => ({
      ...current,
      isRunsLoading: true,
      error: null,
      errorContext: null,
    }));
    try {
      const detail = await apiRequest<IngestionRunDetail>(
        `/curation/ingestion-runs/${runId}`,
        { token: accessToken },
      );
      setState((current) => ({
        ...current,
        isRunsLoading: false,
        selectedRun: detail,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isRunsLoading: false,
        error: resolveErrorMessage(error),
        errorContext: "runs",
      }));
    }
  };

  const saveCorrections = async () => {
    if (!accessToken || !state.selectedRecord || state.isSaving) {
      return;
    }
    if (!canEditRecord) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to edit curation records.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to edit curation records.",
        },
      }));
      return;
    }

    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "save",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));
    try {
      const detail = await apiRequest<CurationRecordDetail>(
        `/curation/records/${state.selectedRecord.record_id}`,
        {
          method: "PATCH",
          token: accessToken,
          body: JSON.stringify({
            title: editState.title,
            provider_name: emptyToNull(editState.provider_name),
            country_code: editState.country_code.toUpperCase(),
            summary: emptyToNull(editState.summary),
            funding_summary: emptyToNull(editState.funding_summary),
            field_tags: parseCsv(editState.field_tags),
            degree_levels: parseCsv(editState.degree_levels),
            citizenship_rules: parseCsv(editState.citizenship_rules),
            min_gpa_value: editState.min_gpa_value
              ? Number(editState.min_gpa_value)
              : null,
            review_notes: emptyToNull(editState.review_notes),
          }),
        },
      );
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        selectedRecord: detail,
        actionFeedback: { variant: "success", message: "Corrections saved." },
        records: current.records.map((item) =>
          item.record_id === detail.record_id ? detail : item,
        ),
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  const importRawRecord = async () => {
    if (!accessToken || state.isSaving) {
      return;
    }
    if (!canImportRaw) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to create raw records.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to create raw records.",
        },
      }));
      return;
    }

    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "import",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));
    try {
      const payload: CurationRawImportRequest = {
        source_key: importState.source_key.trim(),
        source_display_name: importState.source_display_name.trim(),
        source_base_url: importState.source_base_url.trim(),
        source_type: "manual_import",
        title: importState.title.trim(),
        provider_name: emptyToNull(importState.provider_name),
        country_code: importState.country_code.trim().toUpperCase(),
        source_url: importState.source_url.trim(),
        external_source_id: null,
        source_document_ref: null,
        summary: emptyToNull(importState.summary),
        funding_summary: null,
        field_tags: parseCsv(importState.field_tags),
        degree_levels: parseCsv(importState.degree_levels),
        citizenship_rules: [],
        min_gpa_value: null,
        deadline_at: null,
        imported_at: null,
        source_last_seen_at: null,
        review_notes: emptyToNull(importState.review_notes),
        provenance_payload: { imported_via: "curator_dashboard" },
      };

      const detail = await apiRequest<CurationRecordDetail>("/curation/imports", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify(payload),
      });

      setImportState((current) => ({
        ...current,
        source_url: "",
        title: "",
        provider_name: "",
        summary: "",
        review_notes: "",
      }));
      setEditState(buildEditState(detail));
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        filter: "raw",
        selectedRecord: detail,
        actionFeedback: { variant: "success", message: "Raw record created." },
        records:
          current.filter === "raw"
            ? [detail, ...current.records.filter((item) => item.record_id !== detail.record_id)]
            : [detail],
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  const startIngestionRun = async () => {
    if (!accessToken || state.isSaving) {
      return;
    }
    if (!canRunIngestion) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to run ingestion.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to run ingestion.",
        },
      }));
      return;
    }

    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "ingestion",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));
    try {
      const payload: IngestionRunStartRequest = {
        source_key: ingestionState.source_key.trim(),
        source_display_name: emptyToNull(ingestionState.source_display_name),
        source_base_url: emptyToNull(ingestionState.source_base_url),
        source_type: ingestionState.source_type.trim() || "official",
        max_records: Number(ingestionState.max_records) || 5,
        execution_mode: ingestionState.execution_mode,
      };

      const detail = await apiRequest<IngestionRunDetail>("/curation/ingestion-runs", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify(payload),
      });

      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        filter: "raw",
        selectedRun: detail,
        actionFeedback: { variant: "success", message: "Ingestion run started." },
        runs: [detail, ...current.runs.filter((item) => item.run_id !== detail.run_id)],
      }));
      await refreshCurrentFilter(undefined, "raw");
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  const retryIngestionRun = async () => {
    if (!accessToken || !state.selectedRun || state.isSaving) {
      return;
    }
    if (!canRunIngestion) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to retry ingestion runs.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to retry ingestion runs.",
        },
      }));
      return;
    }

    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "ingestion",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));

    try {
      const payload: IngestionRunRetryRequest = {
        max_records: Number(ingestionState.max_records) || null,
        execution_mode: "inline",
      };
      const detail = await apiRequest<IngestionRunDetail>(
        `/curation/ingestion-runs/${state.selectedRun.run_id}/retry`,
        {
          method: "POST",
          token: accessToken,
          body: JSON.stringify(payload),
        },
      );
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        selectedRun: detail,
        runs: [detail, ...current.runs.filter((item) => item.run_id !== detail.run_id)],
        actionFeedback: {
          variant: "success",
          message: "Ingestion run retried successfully.",
        },
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  const toggleRunSelection = (runId: string) => {
    setIngestionBulkState((current) => ({
      ...current,
      selectedRunIds: current.selectedRunIds.includes(runId)
        ? current.selectedRunIds.filter((id) => id !== runId)
        : [...current.selectedRunIds, runId],
    }));
  };

  const assignSelectedRunsQueue = async () => {
    if (!accessToken || ingestionBulkState.selectedRunIds.length === 0 || state.isSaving) {
      return;
    }
    if (!canRunIngestion) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to assign ingestion queues.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to assign ingestion queues.",
        },
      }));
      return;
    }
    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "ingestion",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));
    try {
      const payload: IngestionRunQueueAssignmentRequest = {
        queue_key: ingestionBulkState.queueKey.trim() || "manual-review",
        note: emptyToNull(ingestionBulkState.queueNote),
      };
      const updates = await Promise.all(
        ingestionBulkState.selectedRunIds.map((runId) =>
          apiRequest<IngestionRunDetail>(`/curation/ingestion-runs/${runId}/assign-queue`, {
            method: "POST",
            token: accessToken,
            body: JSON.stringify(payload),
          })
        ),
      );
      const detailById = new Map(updates.map((detail) => [detail.run_id, detail]));
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        selectedRun: current.selectedRun ? detailById.get(current.selectedRun.run_id) ?? current.selectedRun : null,
        runs: current.runs.map((run) => detailById.get(run.run_id) ?? run),
        actionFeedback: {
          variant: "success",
          message: `Assigned queue for ${updates.length} run(s).`,
        },
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  const bulkRetrySelectedRuns = async () => {
    if (!accessToken || ingestionBulkState.selectedRunIds.length === 0 || state.isSaving) {
      return;
    }
    if (!canRunIngestion) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to bulk retry ingestion runs.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to bulk retry ingestion runs.",
        },
      }));
      return;
    }
    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "ingestion",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));
    try {
      const payload: IngestionRunBulkRetryRequest = {
        run_ids: ingestionBulkState.selectedRunIds,
        max_records: Number(ingestionState.max_records) || null,
        execution_mode: "inline",
      };
      const response = await apiRequest<IngestionRunBulkRetryResponse>(
        "/curation/ingestion-runs/bulk-retry",
        {
          method: "POST",
          token: accessToken,
          body: JSON.stringify(payload),
        },
      );
      const updatedDetails = response.items
        .map((item) => item.detail)
        .filter((detail): detail is IngestionRunDetail => detail !== null);
      const detailById = new Map(updatedDetails.map((detail) => [detail.run_id, detail]));
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        selectedRun: current.selectedRun ? detailById.get(current.selectedRun.run_id) ?? current.selectedRun : null,
        runs: current.runs.map((run) => detailById.get(run.run_id) ?? run),
        actionFeedback: {
          variant: response.failed > 0 ? "error" : "success",
          message: `Bulk retry: ${response.retried} retried, ${response.skipped} skipped, ${response.failed} failed.`,
        },
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  const runAction = async (
    action: "approve" | "reject" | "publish" | "unpublish",
  ) => {
    if (!accessToken || !state.selectedRecord || state.isSaving) {
      return;
    }
    if (!canTransitionRecord) {
      setState((current) => ({
        ...current,
        error: "You do not have permission to transition curation records.",
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: "You do not have permission to transition curation records.",
        },
      }));
      return;
    }

    setState((current) => ({
      ...current,
      isSaving: true,
      activeAction: "transition",
      error: null,
      errorContext: null,
      actionFeedback: null,
    }));
    try {
      await apiRequest<CurationRecordDetail>(
        `/curation/records/${state.selectedRecord.record_id}/${action}`,
        {
          method: "POST",
          token: accessToken,
          body: JSON.stringify({ note: emptyToNull(editState.review_notes) }),
        },
      );
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        actionFeedback: { variant: "success", message: transitionSuccessMessage(action) },
      }));
      await refreshCurrentFilter();
    } catch (error) {
      setState((current) => ({
        ...current,
        isSaving: false,
        activeAction: null,
        error: resolveErrorMessage(error),
        errorContext: "action",
        actionFeedback: {
          variant: "error",
          message: resolveErrorMessage(error),
        },
      }));
    }
  };

  return (
    <AppShell
      title="Review, correct, and promote scholarship records."
      description="Only published records reach users. Raw and validated states stay internal."
      eyebrow="Curation"
    >
      <section className="curation-hero" data-testid="curation-dashboard-shell">
        <div>
          <p className="section-eyebrow">Curation posture</p>
          <h2 className="section-title">
            Raw data stays internal until reviewed.
          </h2>
          <p className="body-copy">
            Published records are the only user-facing state.
          </p>
        </div>
        <div className="curation-hero__badges">
          <StatusBadge label="Admin only" variant="validated" />
          <StatusBadge label="Published is user-facing" variant="generated" />
        </div>
      </section>

      {state.actionFeedback ? (
        <FeedbackNotice
          message={state.actionFeedback.message}
          variant={state.actionFeedback.variant}
        />
      ) : null}

      {state.error && state.errorContext === "action" ? (
        <ErrorState
          description={state.error}
          testId="curation-error"
          title="The review workspace needs attention."
        />
      ) : null}

      <section className="page-grid">
        <article className="surface-card" data-testid="curation-ingestion-panel">
          <PageHeader
            eyebrow="Source ingestion"
            title="Import records from a configured source"
            description="Select a source, run the importer, and review the new raw records."
          />
          <div className="form-grid">
            <label className="form-field">
              <span className="form-field__label">Source preset</span>
              <select
                className="text-input"
                onChange={(event) => {
                  const selected =
                    CURATION_SOURCE_OPTIONS.find(
                      (option) => option.source_key === event.target.value,
                    ) ?? CURATION_SOURCE_OPTIONS[0];
                  setIngestionState({
                    source_key: selected.source_key,
                    source_display_name: selected.source_display_name,
                    source_base_url: selected.source_base_url,
                    source_type: selected.source_type,
                    max_records: ingestionState.max_records,
                    execution_mode: ingestionState.execution_mode,
                  });
                }}
                value={ingestionState.source_key}
              >
                {CURATION_SOURCE_OPTIONS.map((option) => (
                  <option key={option.source_key} value={option.source_key}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span className="form-field__label">Source key</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setIngestionState((current) => ({
                    ...current,
                    source_key: event.target.value,
                  }))
                }
                value={ingestionState.source_key}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Display name</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setIngestionState((current) => ({
                    ...current,
                    source_display_name: event.target.value,
                  }))
                }
                value={ingestionState.source_display_name}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Source base URL</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setIngestionState((current) => ({
                    ...current,
                    source_base_url: event.target.value,
                  }))
                }
                value={ingestionState.source_base_url}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Source type</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setIngestionState((current) => ({
                    ...current,
                    source_type: event.target.value,
                  }))
                }
                value={ingestionState.source_type}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Max raw records</span>
              <input
                className="text-input"
                inputMode="numeric"
                onChange={(event) =>
                  setIngestionState((current) => ({
                    ...current,
                    max_records: event.target.value,
                  }))
                }
                value={ingestionState.max_records}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Execution mode</span>
              <select
                className="text-input"
                onChange={(event) =>
                  setIngestionState((current) => ({
                    ...current,
                    execution_mode: event.target.value as IngestionExecutionMode,
                  }))
                }
                value={ingestionState.execution_mode}
              >
                <option value="auto">Auto (queue first)</option>
                <option value="worker">Worker only</option>
                <option value="inline">Inline only</option>
              </select>
            </label>
          </div>
          <div className="document-actions">
            <button
              className="auth-link auth-link--primary"
              data-testid="curation-start-ingestion"
              disabled={state.isSaving || !canRunIngestion}
              onClick={() => void startIngestionRun()}
              type="button"
            >
              {state.activeAction === "ingestion" ? "Running import" : "Run ingestion"}
            </button>
          </div>
        </article>

        <article className="surface-panel">
          <PageHeader
            eyebrow="Recent runs"
            title="Ingestion history"
            description="Each run tracks source, records found, created, and skipped."
          />
          <div className="form-grid">
            <label className="form-field">
              <span className="form-field__label">Run status</span>
              <select
                className="text-input"
                onChange={(event) =>
                  setRunFilterState((current) => ({
                    ...current,
                    status: event.target.value as RunFilterState["status"],
                  }))
                }
                value={runFilterState.status}
              >
                <option value="all">All statuses</option>
                <option value="queued">Queued</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="partial">Partial</option>
                <option value="failed">Failed</option>
              </select>
            </label>
            <label className="form-field">
              <span className="form-field__label">Source key filter</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setRunFilterState((current) => ({
                    ...current,
                    source_key: event.target.value,
                  }))
                }
                placeholder="waterloo-awards"
                value={runFilterState.source_key}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Dispatch status filter</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setRunFilterState((current) => ({
                    ...current,
                    dispatch_status: event.target.value,
                  }))
                }
                placeholder="queued / retry_inline"
                value={runFilterState.dispatch_status}
              />
            </label>
          </div>
          <div className="form-grid">
            <label className="form-field">
              <span className="form-field__label">Queue key</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setIngestionBulkState((current) => ({
                    ...current,
                    queueKey: event.target.value,
                  }))
                }
                placeholder="manual-review"
                value={ingestionBulkState.queueKey}
              />
            </label>
            <label className="form-field">
              <span className="form-field__label">Queue assignment note</span>
              <input
                className="text-input"
                onChange={(event) =>
                  setIngestionBulkState((current) => ({
                    ...current,
                    queueNote: event.target.value,
                  }))
                }
                placeholder="optional note"
                value={ingestionBulkState.queueNote}
              />
            </label>
          </div>
          <div className="document-actions">
            <button
              className="auth-link auth-link--secondary"
              data-testid="curation-assign-queue-selected"
              disabled={
                state.isSaving ||
                !canRunIngestion ||
                ingestionBulkState.selectedRunIds.length === 0
              }
              onClick={() => void assignSelectedRunsQueue()}
              type="button"
            >
              {state.activeAction === "ingestion"
                ? "Assigning queue"
                : `Assign queue to selected (${ingestionBulkState.selectedRunIds.length})`}
            </button>
            <button
              className="auth-link auth-link--primary"
              data-testid="curation-bulk-retry-selected"
              disabled={
                state.isSaving ||
                !canRunIngestion ||
                ingestionBulkState.selectedRunIds.length === 0
              }
              onClick={() => void bulkRetrySelectedRuns()}
              type="button"
            >
              {state.activeAction === "ingestion"
                ? "Retrying selected"
                : `Retry selected runs (${ingestionBulkState.selectedRunIds.length})`}
            </button>
          </div>
          {state.isRunsLoading ? (
            <div className="surface-list">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : state.error && state.errorContext === "runs" ? (
            <ErrorState
              description={state.error}
              title="Unable to load ingestion runs."
              testId="curation-runs-error"
            />
          ) : state.runs.length > 0 ? (
            <div className="curation-list">
              {state.runs.map((run) => (
                <button
                  className={
                    state.selectedRun?.run_id === run.run_id
                      ? "curation-list__item curation-list__item--active"
                      : "curation-list__item"
                  }
                  key={run.run_id}
                  onClick={() => void loadIngestionRun(run.run_id)}
                  type="button"
                >
                  <div className="meta-row">
                    <label
                      aria-label={`Select ingestion run ${run.run_id}`}
                      className="route-card__label"
                      onClick={(event) => event.stopPropagation()}
                    >
                      <input
                        checked={ingestionBulkState.selectedRunIds.includes(run.run_id)}
                        onChange={() => toggleRunSelection(run.run_id)}
                        type="checkbox"
                      />
                    </label>
                    <StatusBadge label={run.status} variant={runBadgeVariant(run.status)} />
                    <span className="route-card__label">{run.source_key}</span>
                  </div>
                  <h3 className="route-card__title">{run.source_display_name}</h3>
                  <p className="route-card__description">
                    Created {run.records_created} · Skipped {run.records_skipped} ·{" "}
                    {run.execution_mode_selected ?? "mode-unknown"}
                  </p>
                  <p className="route-card__description">
                    Queue {run.review_queue ?? "unassigned"}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No recent ingestion runs"
              description="Importer logs and record capture counts will appear here once a source has been parsed."
            />
          )}
          {state.selectedRun ? (
            <article className="data-callout">
              <p className="list-label">Latest run detail</p>
              <p className="body-copy">
                {state.selectedRun.source_display_name} used{" "}
                {state.selectedRun.capture_mode ?? "unknown"} capture and{" "}
                {state.selectedRun.parser_name ?? "unknown"} parsing.
              </p>
              <ul className="detail-list">
                <li>Found: {state.selectedRun.records_found}</li>
                <li>Created: {state.selectedRun.records_created}</li>
                <li>Skipped: {state.selectedRun.records_skipped}</li>
                <li>
                  Requested mode:{" "}
                  {state.selectedRun.execution_mode_requested ?? "unspecified"}
                </li>
                <li>
                  Selected mode:{" "}
                  {state.selectedRun.execution_mode_selected ?? "unknown"}
                </li>
                <li>
                  Dispatch status: {state.selectedRun.dispatch_status ?? "n/a"}
                </li>
                <li>
                  Celery task id: {state.selectedRun.celery_task_id ?? "n/a"}
                </li>
                <li>
                  Attempt count: {state.selectedRun.attempt_count ?? "n/a"}
                </li>
                <li>
                  Retry count: {state.selectedRun.run_retry_count ?? "n/a"}
                </li>
                <li>
                  Last started:{" "}
                  {state.selectedRun.last_started_at
                    ? new Date(state.selectedRun.last_started_at).toLocaleString()
                    : "n/a"}
                </li>
                <li>
                  Last retry requested:{" "}
                  {state.selectedRun.last_retry_requested_at
                    ? new Date(state.selectedRun.last_retry_requested_at).toLocaleString()
                    : "n/a"}
                </li>
                <li>
                  Failure phase: {state.selectedRun.failure_phase ?? "n/a"}
                </li>
                <li>Review queue: {state.selectedRun.review_queue ?? "unassigned"}</li>
                <li>
                  Queue assigned by: {state.selectedRun.queue_assigned_by_user_id ?? "n/a"}
                </li>
                <li>
                  Queue assigned at:{" "}
                  {state.selectedRun.queue_assigned_at
                    ? new Date(state.selectedRun.queue_assigned_at).toLocaleString()
                    : "n/a"}
                </li>
                <li>
                  Queue note: {state.selectedRun.queue_assignment_note ?? "n/a"}
                </li>
                <li>
                  Completed:{" "}
                  {state.selectedRun.completed_at
                    ? new Date(state.selectedRun.completed_at).toLocaleString()
                    : "Still running"}
                </li>
              </ul>
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  data-testid="curation-retry-ingestion"
                  disabled={
                    state.isSaving ||
                    !canRunIngestion ||
                    state.selectedRun.status === "running"
                  }
                  onClick={() => void retryIngestionRun()}
                  type="button"
                >
                  {state.activeAction === "ingestion" ? "Retrying run" : "Retry run"}
                </button>
              </div>
            </article>
          ) : null}
        </article>
      </section>

      <section className="surface-card" data-testid="curation-import-panel">
        <PageHeader
          eyebrow="Manual import"
          title="Add one raw record manually"
          description="Use when a source needs a hand-entered correction or a one-off record."
        />
        <div className="form-grid">
          <label className="form-field">
            <span className="form-field__label">Source key</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  source_key: event.target.value,
                }))
              }
              value={importState.source_key}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Source display name</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  source_display_name: event.target.value,
                }))
              }
              value={importState.source_display_name}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Source base URL</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  source_base_url: event.target.value,
                }))
              }
              value={importState.source_base_url}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Source URL</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  source_url: event.target.value,
                }))
              }
              placeholder="https://example.edu/scholarships/data-science-award"
              value={importState.source_url}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Title</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  title: event.target.value,
                }))
              }
              value={importState.title}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Provider</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  provider_name: event.target.value,
                }))
              }
              value={importState.provider_name}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Country</span>
            <input
              className="text-input"
              maxLength={2}
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  country_code: event.target.value,
                }))
              }
              value={importState.country_code}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Field tags</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  field_tags: event.target.value,
                }))
              }
              value={importState.field_tags}
            />
          </label>
          <label className="form-field">
            <span className="form-field__label">Degree levels</span>
            <input
              className="text-input"
              onChange={(event) =>
                setImportState((current) => ({
                  ...current,
                  degree_levels: event.target.value,
                }))
              }
              value={importState.degree_levels}
            />
          </label>
        </div>
        <label className="form-field">
          <span className="form-field__label">Imported summary</span>
          <textarea
            className="text-area"
            onChange={(event) =>
              setImportState((current) => ({
                ...current,
                summary: event.target.value,
              }))
            }
            rows={5}
            value={importState.summary}
          />
        </label>
        <label className="form-field">
          <span className="form-field__label">Import notes</span>
          <textarea
            className="text-area"
            onChange={(event) =>
              setImportState((current) => ({
                ...current,
                review_notes: event.target.value,
              }))
            }
            rows={3}
            value={importState.review_notes}
          />
        </label>
        <div className="document-actions">
          <button
            className="auth-link auth-link--primary"
            data-testid="curation-import"
            disabled={state.isSaving || !canImportRaw}
            onClick={() => void importRawRecord()}
            type="button"
          >
            {state.activeAction === "import" ? "Importing" : "Create raw record"}
          </button>
        </div>
      </section>

      <section className="curation-grid">
        <article className="surface-card">
          <PageHeader
            eyebrow="Records"
            title="Filter by lifecycle state"
            description="Raw → Validated → Published → Archived."
          />
          <div className="toggle-row">
            {FILTERS.map((filter) => (
              <button
                className={
                  state.filter === filter
                    ? "toggle-chip toggle-chip--active"
                    : "toggle-chip"
                }
                key={filter}
                onClick={() =>
                  setState((current) => ({
                    ...current,
                    filter,
                    selectedRecord: null,
                  }))
                }
                type="button"
              >
                {filter}
              </button>
            ))}
          </div>
          {state.isLoading ? (
            <div className="curation-list">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : state.error && state.errorContext === "records" ? (
            <ErrorState
              description={state.error}
              title="Unable to load curation records."
              testId="curation-records-error"
            />
          ) : state.records.length > 0 ? (
            <div className="curation-list">
              {state.records.map((record) => (
                <button
                  className={
                    record.record_id === selectedId
                      ? "curation-list__item curation-list__item--active"
                      : "curation-list__item"
                  }
                  data-testid={`curation-record-${record.record_state}`}
                  key={record.record_id}
                  onClick={() => void loadRecord(record.record_id)}
                  type="button"
                >
                  <div className="meta-row">
                    <StatusBadge
                      label={record.record_state}
                      variant={badgeVariant(record.record_state)}
                    />
                    <span className="route-card__label">{record.country_code}</span>
                  </div>
                  <h3 className="route-card__title">{record.title}</h3>
                  <p className="route-card__description">
                    {record.provider_name ?? "Provider not listed"}
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No records found"
              description={`There are currently no records in the ${state.filter} state.`}
            />
          )}
        </article>

        <article className="surface-panel" data-testid="curation-record-detail">
          <PageHeader
            eyebrow="Detail"
            title="Review one record"
            description="Correct fields, add notes, then approve or reject."
          />
          {state.isDetailLoading ? (
            <div className="form-grid">
              <SkeletonLine count={6} />
              <SkeletonLine count={4} />
            </div>
           ) : state.error && state.errorContext === "detail" ? (
             <ErrorState
               description={state.error}
               title="Unable to load record detail."
               testId="curation-detail-error"
             />
           ) : state.selectedRecord ? (
             <div className="surface-list">
              <article>
                <div className="meta-row">
                  <StatusBadge
                    label={state.selectedRecord.record_state}
                    variant={badgeVariant(state.selectedRecord.record_state)}
                  />
                  <span className="route-card__label">
                    Source type {state.selectedRecord.source_type ?? "unknown"}
                  </span>
                </div>
                <p className="body-copy">{state.selectedRecord.source_url}</p>
              </article>
              <div className="form-grid">
                <label className="form-field">
                  <span className="form-field__label">Title</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({ ...current, title: event.target.value }))
                    }
                    value={editState.title}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Provider</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        provider_name: event.target.value,
                      }))
                    }
                    value={editState.provider_name}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Country</span>
                  <input
                    className="text-input"
                    maxLength={2}
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        country_code: event.target.value,
                      }))
                    }
                    value={editState.country_code}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Minimum GPA</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        min_gpa_value: event.target.value,
                      }))
                    }
                    value={editState.min_gpa_value}
                  />
                </label>
              </div>
              <label className="form-field">
                <span className="form-field__label">Summary</span>
                <textarea
                  className="text-area"
                  onChange={(event) =>
                    setEditState((current) => ({ ...current, summary: event.target.value }))
                  }
                  rows={6}
                  value={editState.summary}
                />
              </label>
              <div className="form-grid">
                <label className="form-field">
                  <span className="form-field__label">Field tags</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({ ...current, field_tags: event.target.value }))
                    }
                    placeholder="data science, analytics"
                    value={editState.field_tags}
                  />
                </label>
                <label className="form-field">
                  <span className="form-field__label">Degree levels</span>
                  <input
                    className="text-input"
                    onChange={(event) =>
                      setEditState((current) => ({
                        ...current,
                        degree_levels: event.target.value,
                      }))
                    }
                    placeholder="MS"
                    value={editState.degree_levels}
                  />
                </label>
              </div>
              <label className="form-field">
                <span className="form-field__label">Citizenship rules</span>
                <input
                  className="text-input"
                  onChange={(event) =>
                    setEditState((current) => ({
                      ...current,
                      citizenship_rules: event.target.value,
                    }))
                  }
                  placeholder="PK, IN"
                  value={editState.citizenship_rules}
                />
              </label>
              <label className="form-field">
                <span className="form-field__label">Reviewer notes</span>
                <textarea
                  className="text-area"
                  data-testid="curation-review-notes"
                  onChange={(event) =>
                    setEditState((current) => ({
                      ...current,
                      review_notes: event.target.value,
                    }))
                  }
                  rows={4}
                  value={editState.review_notes}
                />
              </label>
              <div className="document-actions">
                <button
                  className="auth-link auth-link--secondary"
                  data-testid="curation-save"
                  disabled={state.isSaving || !canEditRecord}
                  onClick={() => void saveCorrections()}
                  type="button"
                >
                  {state.activeAction === "save" ? "Saving" : "Save corrections"}
                </button>
                {actionButtons.map((item) => (
                  <button
                    className={`auth-link ${item.variant}`}
                    data-testid={`curation-${item.action}`}
                    disabled={state.isSaving || !canTransitionRecord}
                    key={item.action}
                    onClick={() =>
                      void runAction(
                        item.action as "approve" | "reject" | "publish" | "unpublish",
                      )
                    }
                    type="button"
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState
              title="No record selected"
              description="Select a record from the list to review its fields and change its state."
            />
          )}
        </article>
      </section>

      <section className="surface-card">
        <PageHeader
          eyebrow="About"
          title="Why this workflow is narrow"
          description="State enforcement and publish control over analytics-heavy tooling."
        />
        <div className="split-panel">
          <article className="data-callout">
            <p className="list-label">Source-of-truth rule</p>
            <p className="body-copy">
              Only published records reach users. Raw records stay internal.
            </p>
          </article>
          <article className="guidance-callout">
            <p className="list-label">Curator responsibility</p>
            <p className="body-copy">
              Review notes and explicit state changes provide minimum traceability.
            </p>
          </article>
        </div>
      </section>
    </AppShell>
  );
}

function buildEditState(record: CurationRecordDetail): EditState {
  return {
    title: record.title,
    provider_name: record.provider_name ?? "",
    country_code: record.country_code,
    summary: record.summary ?? "",
    funding_summary: record.funding_summary ?? "",
    field_tags: record.field_tags.join(", "),
    degree_levels: record.degree_levels.join(", "),
    citizenship_rules: record.citizenship_rules.join(", "),
    min_gpa_value: record.min_gpa_value?.toString() ?? "",
    review_notes: record.review_notes ?? "",
  };
}

function parseCsv(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function emptyToNull(value: string) {
  const normalized = value.trim();
  return normalized ? normalized : null;
}

function badgeVariant(state: CurationRecordState) {
  if (state === "published") {
    return "validated";
  }
  if (state === "validated") {
    return "generated";
  }
  if (state === "archived") {
    return "warning";
  }
  return "planned";
}

function runBadgeVariant(status: IngestionRunSummary["status"]) {
  if (status === "completed") {
    return "validated";
  }
  if (status === "partial") {
    return "generated";
  }
  if (status === "failed") {
    return "warning";
  }
  return "planned";
}

function transitionSuccessMessage(action: "approve" | "reject" | "publish" | "unpublish") {
  if (action === "approve") {
    return "Record approved successfully.";
  }
  if (action === "reject") {
    return "Record rejected successfully.";
  }
  if (action === "publish") {
    return "Record published successfully.";
  }
  return "Record unpublished successfully.";
}

function resolveErrorMessage(error: unknown) {
  if (typeof error === "object" && error !== null && "message" in error) {
    return (error as ApiError).message;
  }
  return "Unexpected curation failure";
}
