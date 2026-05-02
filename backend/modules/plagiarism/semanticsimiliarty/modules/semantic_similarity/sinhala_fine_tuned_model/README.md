---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:260
- loss:CosineSimilarityLoss
base_model: sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens
widget:
- source_sentence: සෞඛ්‍ය සම්පන්න දිවියකට ජලය පානය කිරීම වැදගත් වේ
  sentences:
  - සෞඛ්‍යය රැකගැනීමට ප්‍රමාණවත් ජලය පානය කළ යුතුය
  - වෛද්‍ය පර්යේෂණ මගින් මාරාන්තික රෝග සඳහා නව ඖෂධ සොයා ගනී
  - විදේශ ආයෝජන මගින් රටකට නව තාක්ෂණය සහ ප්‍රාග්ධනය ලැබේ
- source_sentence: සීගිරිය යනු ලොව පුරා ප්‍රසිද්ධ ඓතිහාසික ස්ථානයකි
  sentences:
  - නීතිය සමාජයේ සාමය සහ සාධාරණත්වය රැක ගනී
  - සමාජ මාධ්‍ය භාවිතය පුද්ගල සබඳතා කෙරෙහි බලපෑම් ඇති කරයි
  - මහනුවර නගරය කඳුකර ප්‍රදේශයේ පිහිටා ඇත
- source_sentence: සාහිත්‍යය මගින් මිනිසාගේ චින්තනය සහ රසඥතාව වර්ධනය වේ
  sentences:
  - නවීන යන්ත්‍රෝපකරණ භාවිතයෙන් කෘෂිකාර්මික අස්වැන්න වැඩි කළ හැක
  - සතුන් සුරැකීමෙන් ස්වභාවධර්මයේ සමතුලිතතාවය ආරක්ෂා කර ගත හැක
  - ප්‍රජාතන්ත්‍රවාදය යනු ජනතාවගේ පාලනය ජනතාව විසින්ම සිදු කිරීමයි
- source_sentence: සාහිත්‍යය මගින් මිනිසාගේ චින්තනය සහ රසඥතාව වර්ධනය වේ
  sentences:
  - බැංකු ක්ෂේත්‍රය ඩිජිටල්කරණය වීම නිසා මුදල් ගනුදෙනු පහසු වී ඇත
  - තාක්ෂණික දියුණුව වැඩිවීම නිසා වැඩ කාර්යක්ෂමතාව ඉහළ යයි
  - අධ්‍යාපනය රටක සංවර්ධනයට මූලික වේ
- source_sentence: සාම්ප්‍රදායික නර්තන කලාව අපේ සංස්කෘතියේ වටිනා උරුමයකි
  sentences:
  - ඛනිජ තෙල් භාවිතය සීමා කිරීම පරිසර දූෂණය අවම කිරීමට හේතු වේ
  - පුනර්ජනනීය බලශක්තිය භාවිතය මගින් විදුලි අර්බුදයට විසඳුම් සෙවිය හැක
  - ආර්ථික වර්ධනය ජන ජීවන මට්ටම ඉහළ නැංවීමට උපකාරී වේ
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens](https://huggingface.co/sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens). It maps sentences & paragraphs to a 768-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens](https://huggingface.co/sentence-transformers/xlm-r-100langs-bert-base-nli-stsb-mean-tokens) <!-- at revision 88b1aae5fcf203597dfbe40144aaed61833bc017 -->
- **Maximum Sequence Length:** 128 tokens
- **Output Dimensionality:** 768 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 128, 'do_lower_case': False, 'architecture': 'XLMRobertaModel'})
  (1): Pooling({'word_embedding_dimension': 768, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'සාම්ප්\u200dරදායික නර්තන කලාව අපේ සංස්කෘතියේ වටිනා උරුමයකි',
    'පුනර්ජනනීය බලශක්තිය භාවිතය මගින් විදුලි අර්බුදයට විසඳුම් සෙවිය හැක',
    'ඛනිජ තෙල් භාවිතය සීමා කිරීම පරිසර දූෂණය අවම කිරීමට හේතු වේ',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 768]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[ 1.0000, -0.0229,  0.1619],
#         [-0.0229,  1.0000,  0.4029],
#         [ 0.1619,  0.4029,  1.0000]])
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 260 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 260 samples:
  |         | sentence_0                                                                        | sentence_1                                                                        | label                                                          |
  |:--------|:----------------------------------------------------------------------------------|:----------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                            | string                                                                            | float                                                          |
  | details | <ul><li>min: 7 tokens</li><li>mean: 15.62 tokens</li><li>max: 23 tokens</li></ul> | <ul><li>min: 9 tokens</li><li>mean: 16.72 tokens</li><li>max: 27 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.25</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                      | sentence_1                                                              | label            |
  |:--------------------------------------------------------------------------------|:------------------------------------------------------------------------|:-----------------|
  | <code>පුනර්ජනනීය බලශක්තිය භාවිතය මගින් විදුලි අර්බුදයට විසඳුම් සෙවිය හැක</code> | <code>ගුවන් යානා තාක්ෂණය ලෝකය පුරා ගමනාගමනය පහසු කර ඇත</code>           | <code>0.0</code> |
  | <code>ශ්‍රී ලංකාව ඉන්දියන් සාගරයේ පිහිටි දූපතකි</code>                          | <code>පෞරාණික ස්ථාන විනාශ කිරීම නීතියෙන් දඬුවම් ලැබිය හැකි වරදකි</code> | <code>0.0</code> |
  | <code>ජල සම්පත් සුරැකීම පරිසරය රැක ගැනීමට වැදගත් වේ</code>                      | <code>ජලය වියළීමෙන් පරිසරයට හානියක් සිදු විය හැක</code>                 | <code>0.6</code> |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 4
- `per_device_eval_batch_size`: 4
- `num_train_epochs`: 1
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 4
- `per_device_eval_batch_size`: 4
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 1
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `project`: huggingface
- `trackio_space_id`: trackio
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: no
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: True
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Framework Versions
- Python: 3.10.0
- Sentence Transformers: 5.1.2
- Transformers: 4.57.2
- PyTorch: 2.9.1+cpu
- Accelerate: 1.12.0
- Datasets: 4.4.1
- Tokenizers: 0.22.1

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->